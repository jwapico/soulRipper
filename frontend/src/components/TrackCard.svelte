<script lang="ts">
	import type { TrackResponse } from "$lib/interfaces/TrackResponse";
	import Player from "./Player.svelte";
    let audio = $state<HTMLAudioElement | null>(null);
    function play(): void {
        if (!audio) 
            audio = new Audio(`file://${track.filepath}`)

        audio?.play()
    }

    let { track }: {track: TrackResponse} = $props();
</script>

<div class="flex">
    <!-- <button onclick={play}>playss</button> -->
    <Player src={track.filepath} title={track.title} artist={track.artists} />
    <!-- <div>{track.title}</div>
    <div>{track.artists}</div>
    <div>{track.album}</div>
    <div>{track.date_added}</div>
    <div>{track.filepath}</div> -->
</div>