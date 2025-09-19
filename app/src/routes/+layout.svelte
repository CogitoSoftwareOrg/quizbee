<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';

	import ThemeController from '$lib/features/ThemeController.svelte';

	let { children } = $props();
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<ThemeController />
{@render children?.()}
