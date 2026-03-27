<script>
    let { data } = $props();
</script>

<h1>soulripper ui</h1>

{#each data.tracks as track}
    <div>
        <p>{track.id} {track.title} {track.spotify_id}</p>
        <a href={track.filepath}>{track.filepath}</a>
    </div>
{/each}