<script>
	import { onMount } from 'svelte';
	import { Preferences } from '@capacitor/preferences';

	const LIGHT_THEME = 'QUIZBEE_LIGHT';
	const DARK_THEME = 'QUIZBEE_DARK';

	onMount(async () => {
		const theme = await Preferences.get({ key: 'theme' });
		theme.value = theme.value || LIGHT_THEME;
		document.documentElement.setAttribute('data-theme', theme.value);
		Preferences.set({ key: 'theme', value: theme.value });
	});
</script>
