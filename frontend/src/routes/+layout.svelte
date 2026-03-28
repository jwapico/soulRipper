<script lang="ts">
	import Sidebar from '../components/Sidebar.svelte';
	import Topbar from '../components/Topbar.svelte';

	let { children } = $props();
</script>

<!-- TODO: CSS to be moved into files -->

<div style="display: flex; flex-direction: column; border: 1px solid orange">
	<Topbar style="border: 1px solid yellow">
		<p>File</p>
		<p>Preferences</p>
	</Topbar>

	<div style="display: flex; border: 1px solid red">
		<Sidebar style="border: 1px solid blue">
			<a href="/">tracks</a>
			<a href="/playlists">playlists</a>
			<a href="/download">download</a>
		</Sidebar>
		
		{@render children()}
	</div>
</div>