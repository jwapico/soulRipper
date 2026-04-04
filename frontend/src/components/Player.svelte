<!-- rust api in src-tauri/src/audio.rs -->

<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { invoke } from '@tauri-apps/api/core';
    import { listen, type UnlistenFn } from '@tauri-apps/api/event';
    import type { PlaybackState } from '$lib/interfaces/PlaybackState';

    let is_playing = $state(false);
    let position = $state(0);
    let isDragging = $state(false);
    let isSeeking = $state(false);
    let duration = $state<number | null>(null);
    let filepath = $state<string | null>(null);

    let currentTime = $derived(formatTime(position));
    let totalTime = $derived(duration ? formatTime(duration) : '--:--');

    let unlistenPosition: UnlistenFn;
    let unlistenTrackEnd: UnlistenFn;

    function formatTime(seconds: number): string {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    async function togglePlayPause() {
        try {
            if (is_playing)
                await invoke('pause_audio');
            else
                await invoke('resume_audio');
        } catch (e) {
            console.error('Toggle play/pause failed:', e);
        }
    }

    function handleSeekInput(event: Event) {
        const input = event.target as HTMLInputElement;
        position = parseFloat(input.value);
    }

    async function handleSeekCommit(event: Event) {
      const input = event.target as HTMLInputElement;
      const seekPosition = parseFloat(input.value);
      
      try {
          isSeeking = true;
          await invoke('seek_audio', { positionSecs: seekPosition });
      } catch (e) {
          console.error('Seek failed:', e);
          await revertSlider();
      } finally {
          isSeeking = false;
      }
    }

    async function revertSlider() {
        try {
            const state: PlaybackState = await invoke('get_playback_state');
            position = state.position;
            duration = state.duration;
            is_playing = state.state === 'playing';
        } catch (e) {
            console.error('Failed to revert slider:', e);
        }
    }

    onMount(async () => {
        try {
            const state: PlaybackState = await invoke('get_playback_state');
            is_playing = state.state === 'playing';
            position = state.position;
            duration = state.duration;
            filepath = state.filepath;
        } catch (e) {
            console.error('Failed to get initial playback state:', e);
        }

        unlistenPosition = await listen('audio://position_update', (event) => {
            const payload = event.payload as {
                position: number;
                duration: number | null;
                state: string;
            };

            if (!isDragging && !isSeeking)
                position = payload.position;
            
            duration = payload.duration;
            is_playing = payload.state === 'playing';
        });

        unlistenTrackEnd = await listen('audio://track_ended', (event) => {
            const payload = event.payload as { filepath: string | null };
            position = 0;
            is_playing = false;
            
        });
    });

    onDestroy(() => {
        if (unlistenPosition) unlistenPosition();
        if (unlistenTrackEnd) unlistenTrackEnd();
    });

    function handleMouseDown() { isDragging = true; }
    function handleMouseUp() { isDragging = false; }
    function handleTouchStart() { isDragging = true; }
    function handleTouchEnd() { isDragging = false; }
</script>

<div class="player">
    <button onclick={togglePlayPause}>
        {is_playing ? '⏸' : '▶'}
    </button>

    <span class="time">{currentTime}</span>

    <input
        type="range"
        min="0"
        max={duration ?? 0}
        step="0.1"
        value={position}
        oninput={handleSeekInput}
        onchange={handleSeekCommit}
        onmousedown={handleMouseDown}
        onmouseup={handleMouseUp}
        ontouchstart={handleTouchStart}
        ontouchend={handleTouchEnd}
        class="slider"
    />

    <span class="time">{totalTime}</span>
</div>

<style>
    .player {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 60px;
        background: #1a1a1a;
        color: white;
        display: flex;
        align-items: center;
        padding: 0 1rem;
        gap: 0.5rem;
        z-index: 1000;
    }

    button {
        background: transparent;
        border: 1px solid #555;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
    }

    .slider {
        flex: 1;
        margin: 0 1rem;
        cursor: pointer;
    }

    .time {
        min-width: 4rem;
        text-align: center;
        font-family: monospace;
    }
</style>