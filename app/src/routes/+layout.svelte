<script lang="ts">
	import '../app.css';
	import '$lib/pb/pb-on-change';

	import { fly } from 'svelte/transition';
	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/state';

	import favicon from '$lib/assets/favicon.svg';
	import PortalHost from '$lib/actions/PortalHost.svelte';

	let { children } = $props();

	afterNavigate(() => {
		console.log('afterNavigate');
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<PortalHost />

{@render children?.()}
