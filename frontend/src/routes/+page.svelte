<script lang="ts">
	import type { TrackResponse } from '$lib/interfaces/TrackResponse.js';
	import TrackCard from '../components/TrackCard.svelte';

    let { data } = $props()
    let tracks: TrackResponse[] = $derived(data.tracks);
</script>

{#each tracks as track}
    <TrackCard {track} />
{/each}