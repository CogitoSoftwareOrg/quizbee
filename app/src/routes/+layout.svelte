<script lang="ts">
	import '../app.css';
	import '$lib/pb/pb-on-change';

	import { afterNavigate } from '$app/navigation';

	import favicon from '$lib/assets/icons/honey.svg';
	import PortalHost from '$lib/actions/PortalHost.svelte';

	let { children } = $props();

	afterNavigate(() => {
		console.log('afterNavigate');
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="preload" as="font" href="/fonts/Roboto-VariableFont.ttf" type="font/ttf"/>
</svelte:head>

<PortalHost />

{@render children?.()}
