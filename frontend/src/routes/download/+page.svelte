<script lang="typescript">
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

<input bind:value={searchQuery} placeholder="Search Query">

<button onclick={downloadTrack}>
    download
</button>

{#if filepath}
    <p>{filepath}</p>
{/if}