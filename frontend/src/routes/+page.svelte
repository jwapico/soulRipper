<script>
    let { data } = $props();
</script>

<h1>soulripper ui</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>

<p>{data.track.id}</p>
<p>{data.track.title}</p>
<p>{data.track.album}</p>
<p>{data.track.filepath}</p>