<script module>
	const LIGHT_THEME = 'QUIZBEE_LIGHT';
	const DARK_THEME = 'QUIZBEE_DARK';

	let selectedDark = $state(false);
</script>

<script lang="ts">
	import { onMount } from 'svelte';
	import { Preferences } from '@capacitor/preferences';
	import { Sun, Moon } from 'lucide-svelte';

	const { expanded = false } = $props();

	const themeLabel = $derived(selectedDark ? 'Dark mode' : 'Light mode');

	onMount(async () => {
		const theme = await Preferences.get({ key: 'theme' });
		theme.value === DARK_THEME ? (selectedDark = true) : (selectedDark = false);
	});

	$effect(() => {
		let newTheme = LIGHT_THEME;
		if (selectedDark) newTheme = DARK_THEME;

		document.documentElement.setAttribute('data-theme', newTheme);
		Preferences.set({ key: 'theme', value: newTheme });
	});
</script>

{#if expanded}
	<label
		class="hover:bg-base-300 border-base-300 flex w-full cursor-pointer items-center gap-3 rounded-lg border px-2 py-1 transition-colors"
	>
		<input
			bind:checked={selectedDark}
			type="checkbox"
			class="theme-controller hidden"
			value={selectedDark ? DARK_THEME : LIGHT_THEME}
		/>

		{#if selectedDark}
			<Moon class="swap-on size-7" />
		{:else}
			<Sun class="swap-off size-7" />
		{/if}

		<span class="text-base-content text-nowrap text-sm font-medium">{themeLabel}</span>
	</label>
{:else}
	<label class="swap swap-rotate cursor-pointer">
		<input
			bind:checked={selectedDark}
			type="checkbox"
			class="theme-controller hidden"
			value={selectedDark ? DARK_THEME : LIGHT_THEME}
		/>

		<Sun class="swap-off size-7" />
		<Moon class="swap-on size-7" />
	</label>
{/if}
