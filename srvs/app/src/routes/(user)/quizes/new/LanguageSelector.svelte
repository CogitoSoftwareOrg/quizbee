<script lang="ts">
	import { Select } from '@quizbee/ui-svelte-daisy';

	interface Props {
		selectedLanguage?: string;
	}

	let { selectedLanguage = $bindable('English') }: Props = $props();

	const languages = [
		{ value: 'English', label: 'English' },
		{ value: 'Spanish', label: 'Español' },
		{ value: 'French', label: 'Français' },
		{ value: 'German', label: 'Deutsch' },
		{ value: 'Italian', label: 'Italiano' },
		{ value: 'Portuguese', label: 'Português' },
		{ value: 'Polish', label: 'Polski' },
		{ value: 'Russian', label: 'Русский' },
		{ value: 'Dutch', label: 'Nederlands' },
		{ value: 'Slovak', label: 'Slovenčina' },
		{ value: 'Hungarian', label: 'Magyar' }
	];
</script>

<div class="w-full">
	<Select bind:value={selectedLanguage} options={languages} class="w-full" />
</div>
