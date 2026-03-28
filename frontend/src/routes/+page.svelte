<script lang="typescript">
    let { data } = $props();

    let searchQuery = $state("")
    let filepath = $state("")

    async function downloadTrack() {
        console.log(JSON.stringify({ query: searchQuery }))

        const response = await fetch("http://localhost:8000/tracks/download", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ query: searchQuery })
        })

        const result = await response.json()
        console.log(result)
        filepath = result.filepath
    }
</script>

<h1>soulripper ui</h1>

<input bind:value={searchQuery} placeholder="Search Query">
<button onclick={downloadTrack}>
    download
</button>

{#if filepath}
    <p>{filepath}</p>
{/if}

{#each data.tracks as track}
    <div>
        <p>{track.id} {track.title} {track.spotify_id}</p>
        <a href={track.filepath}>{track.filepath}</a>
    </div>
{/each}