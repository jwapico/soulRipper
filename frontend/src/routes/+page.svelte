<script lang="ts">
    let { data } = $props();
</script>

{#each data.tracks as track}
    <div>
        <p>{track.id} {track.title} {track.spotify_id}</p>
        <a href={track.filepath}>{track.filepath}</a>
    </div>
{/each}