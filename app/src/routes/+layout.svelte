<script lang="ts">
	import '../app.css';
	import '$lib/pb/pb-on-change';

	import { onMount } from 'svelte';
	import { PortalHost } from '@cogisoft/ui-svelte-daisy';

	import favicon from '$lib/assets/icons/bee_final.svg';
	import ThemeLoad from '$lib/features/ThemeLoad.svelte';
	// import posthog from 'posthog-js';

	let { children } = $props();

	// afterNavigate(() => {
	// 	posthog.capture('page_view', {
	// 		path: page.url.pathname
	// 	});
	// });

	import { registerSW } from 'virtual:pwa-register';
	onMount(() => {
		const updateSW = registerSW({
			immediate: true, // сразу ставим SW
			onRegisteredSW(url: string, reg: ServiceWorkerRegistration) {
				console.log('[PWA] registered:', url, reg);
			},
			onRegisterError(err: Error) {
				console.error('[PWA] register error:', err);
			},
			onNeedRefresh() {
				console.log('[PWA] need refresh');
			},
			onOfflineReady() {
				console.log('[PWA] offline ready');
			}
		});
		// при необходимости: updateSW(true) чтобы применить обновление
	});

	import { pwaInfo } from 'virtual:pwa-info';
	const webManifestLink = $derived(pwaInfo ? pwaInfo.webManifest.linkTag : '');
</script>

<svelte:head>
	{@html webManifestLink}
	<link rel="icon" href={favicon} />
	<link
		rel="preload"
		as="font"
		href="/fonts/League_Spartan/LeagueSpartan-VariableFont_wght.ttf"
		type="font/ttf"
	/>
</svelte:head>

<PortalHost />

<ThemeLoad />

{@render children?.()}
