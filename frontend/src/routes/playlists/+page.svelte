<script lang="ts">
	import type { PlaylistTracksResponse } from '$lib/interfaces/PlaylistTracksResponse.ts';
	import TrackCard from '../../components/TrackCard.svelte';

    let { data } = $props();
    let playlists: PlaylistTracksResponse[] = $derived(data.playlist_tracks)
</script>

<div>playlists</div>

<h1>spotify playlists</h1>

{#each playlists as playlist}
    <h2>{playlist.name}</h2>
    {#each playlist.tracks as track}
        <TrackCard 
            title={track.title ?? null} 
            album={track.album ?? null} 
            artists={track.artists?.join(", ") ?? null} 
            date_added={track.date_added ?? null} 
            filepath={track.filepath ?? null} 
        />
    {/each}
{/each}