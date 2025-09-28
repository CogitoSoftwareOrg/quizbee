<script lang="ts">
	import '../app.css';
	import '$lib/pb/pb-on-change';

	import { afterNavigate } from '$app/navigation';
	import { page } from '$app/state';

	import favicon from '$lib/assets/icons/bee1.svg';
	import PortalHost from '$lib/actions/PortalHost.svelte';
	import posthog from 'posthog-js';

	let { children } = $props();

	afterNavigate(() => {
		posthog.capture('page_view', {
			path: page.url.pathname
		});
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<link
		rel="preload"
		as="font"
		href="/fonts/League_Spartan/LeagueSpartan-VariableFont_wght.ttf"
		type="font/ttf"
	/>
</svelte:head>

<PortalHost />

{@render children?.()}
