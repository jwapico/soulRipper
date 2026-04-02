<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { invoke } from '@tauri-apps/api/core';
  import { listen, type UnlistenFn } from '@tauri-apps/api/event';
  import type { PlaybackState } from '$lib/interfaces/PlaybackState';

  // Reactive state
  let playing = $state(false);
  let position = $state(0);
  let duration = $state<number | null>(null);
  let filepath = $state<string | null>(null);
  let isDragging = $state(false);          // new: true while user drags slider
  let seeking = $state(false);             // new: true while a seek command is in flight

  // Derived display values
  let progress = $derived(duration ? (position / duration) * 100 : 0);
  let currentTime = $derived(formatTime(position));
  let totalTime = $derived(duration ? formatTime(duration) : '--:--');

  let unlistenPosition: UnlistenFn;
  let unlistenTrackEnd: UnlistenFn;

  function formatTime(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  }

  // Toggle play/pause
  async function togglePlayPause() {
    try {
      if (playing) {
        await invoke('pause_audio');
      } else {
        await invoke('resume_audio');
      }
    } catch (e) {
      console.error('Toggle play/pause failed:', e);
    }
  }

  // Called on input (while dragging) – updates slider visually only
  function handleSeekInput(event: Event) {
    const input = event.target as HTMLInputElement;
    position = parseFloat(input.value);   // optimistic UI update
  }

  // Called on change (when user releases mouse/touch) – triggers seek command
  async function handleSeekCommit(event: Event) {
    const input = event.target as HTMLInputElement;
    const seekPosition = parseFloat(input.value);
    seeking = true;
    try {
      await invoke('seek_audio', { positionSecs: seekPosition });
    } catch (e) {
      console.error('Seek failed:', e);
      // Revert slider to actual playback position
      await revertSlider();
    } finally {
      seeking = false;
    }
  }

  // Revert slider to current playback position (after a failed seek)
  async function revertSlider() {
    try {
      const state: PlaybackState = await invoke('get_playback_state');
      position = state.position;
    } catch (e) {
      console.error('Failed to revert slider:', e);
    }
  }

  // Dragging flag management
  function handleMouseDown() { isDragging = true; }
  function handleMouseUp() { isDragging = false; }
  function handleTouchStart() { isDragging = true; }
  function handleTouchEnd() { isDragging = false; }

  // Fetch initial state and set up event listeners
  onMount(async () => {
    try {
      const state: PlaybackState = await invoke('get_playback_state');
      playing = state.state === 'playing';
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
      // Ignore updates while user is dragging or a seek is in flight
      if (!isDragging && !seeking) {
        position = payload.position;
      }
      duration = payload.duration;
      playing = payload.state === 'playing';
    });

    unlistenTrackEnd = await listen('audio://track_ended', (event) => {
      const payload = event.payload as { filepath: string | null };
      position = 0;
      playing = false;
    });
  });

  onDestroy(() => {
    if (unlistenPosition) unlistenPosition();
    if (unlistenTrackEnd) unlistenTrackEnd();
  });
</script>

<div class="player">
  <button onclick={togglePlayPause}>
    {playing ? '⏸' : '▶'}
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
