<script lang="ts">
	import type { TrackResponse } from "$lib/interfaces/TrackResponse";
    import { invoke } from "@tauri-apps/api/core";

    let { track }: {track: TrackResponse} = $props();
    async function play() {
		if (track.filepath) {
            // TODO: Temporary fix for nonlocal filepaths - python3 -m http.server 8080 --directory /home/goop/soulRipper/debug/music &
            // const filename = track.filepath.split("/").pop();
			// await invoke("play_audio", { filepath: `http://10.4.44.50:8080/${filename}` });
			await invoke("play_audio", { filepath: track.filepath });
		}
	}
</script>

<div class="flex">
    <button onclick={play}>play</button>
    <div>{track.title}</div>
    <div>{track.artists}</div>
    <div>{track.album}</div>
    <div>{track.date_added}</div>
    <div>{track.filepath}</div>
</div>