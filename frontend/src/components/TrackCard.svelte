<script lang="ts">
	import type { TrackResponse } from "$lib/interfaces/TrackResponse";

    let { track }: {track: TrackResponse} = $props();
</script>

<div class="flex">
    <button>play</button>
    <div>{track.title}</div>
    <div>{track.artists}</div>
    <div>{track.album}</div>
    <div>{track.date_added}</div>
    <div>{track.filepath}</div>
</div>