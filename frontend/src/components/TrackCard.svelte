<script lang="ts">
    import { invoke } from "@tauri-apps/api/core";

    let { title, artists, album, date_added, filepath }: {title: string | null, artists: string | null, album: string | null, date_added: string | null, filepath: string | null} = $props();
    async function play() {
		if (filepath) {
            // TODO: Temporary fix for nonlocal filepaths - python3 -m http.server 8080 --directory /home/goop/soulRipper/debug/music &
            // const filename = track.filepath.split("/").pop();
			// await invoke("play_audio", { filepath: `http://10.4.44.50:8080/${filename}` });
			await invoke("play_audio", { filepath: filepath });
		}
	}
</script>

<div class="flex">
    <button onclick={play}>play</button>
    <div>{title}</div>
    <div>{artists}</div>
    <div>{album}</div>
    <div>{date_added}</div>
    <div>{filepath}</div>
</div>