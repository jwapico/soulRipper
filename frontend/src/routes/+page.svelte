<script lang="ts">
	import type { AudiofileMetadata } from '$lib/interfaces/AudiofileMetadata';
	import type { TrackResponse } from '$lib/interfaces/TrackResponse.js';
	import TrackCard from '../components/TrackCard.svelte';
    import { invoke } from '@tauri-apps/api/core';
    import { platform } from "@tauri-apps/plugin-os";
    import { open } from "@tauri-apps/plugin-dialog"
    import { listen, type UnlistenFn } from "@tauri-apps/api/event";

    let { data } = $props()
    let db_tracks: TrackResponse[] = $derived(data.tracks);

    let local_library_dirs: string[] = $state([]);
    let local_tracks: AudiofileMetadata[] = $state([])
    let unlisten: UnlistenFn | null = $state(null);

    // open tauri model append selections
    async function select_folder() {
        const selected = await open({
            directory: true,
            multiple: true,
            title: "select music folder(s)"
        })

        if (selected) {
            local_library_dirs = [...local_library_dirs, ...selected]; 
        }
    }

    // invoke the rust scan function
    async function start_local_scan() {
        if (await platform() === "android") {
            // TODO: this should not be hard coded alsoi it doesnt work!
            invoke("scan_dir", { dir: "/storage/eumlated/0/music" });
        } else {
            for (const dir of local_library_dirs) {
                invoke("scan_dir", { dir });
            }
        }
    }

    // create a listener on the scan endpoint which will have the metadata contents of a scanned file
    async function scan_listener() {
        unlisten = await listen<AudiofileMetadata>("scan://file", (event) => {
            local_tracks = [...local_tracks, event.payload];
        })
    }
    
    // attach the listener
    $effect(() => {
        scan_listener();
        return() => { if (unlisten) unlisten() };
    })
</script>

<!-- TODO: everything laggy asf need to not load every single thing at onced -->

<div>
    {#each local_library_dirs as dir, i}
        <span>{dir}</span>
        <button onclick={() => local_library_dirs = local_library_dirs.filter((_, idx) => idx !== i)}>x</button>
    {/each}
</div>

<button onclick={select_folder}>add folder(s)</button>
<button onclick={start_local_scan}>scan local library</button>

{#each local_tracks as track}
    <TrackCard 
        title={track.tags.TrackTitle || null}
        artists={track.tags.TrackArtist || null}
        album={track.tags.AlbumTitle || null}
        date_added={track.created.toString()}
        filepath={track.filepath}
    />
{/each}

{#each db_tracks as track}
    <TrackCard 
        title={track.title || null}
        artists={track.artists?.join(", ") || null}
        album={track.album || null}
        date_added={track.date_added || null}
        filepath={track.filepath || null} 
    />
{/each}
