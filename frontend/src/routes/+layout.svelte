<script lang="ts">
	import '../app.css'

	import Sidebar from '../components/Sidebar.svelte';
	import Topbar from '../components/Topbar.svelte';
	import Player from '../components/Player.svelte';

	let { children } = $props();
</script>

<!-- TODO: CSS to be moved into files -->

<div>
	<Topbar>
		<p>File</p>
		<p>Preferences</p>
	</Topbar>

	<div>
		<Sidebar>
			<a href="/">tracks</a>
			<a href="/playlists">playlists</a>
			<a href="/download">download</a>
		</Sidebar>
		
		{@render children()}
	</div>

	<Player />
</div>