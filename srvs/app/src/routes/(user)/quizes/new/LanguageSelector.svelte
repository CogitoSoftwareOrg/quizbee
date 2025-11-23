<script lang="ts">
	import { Select } from '@quizbee/ui-svelte-daisy';

	interface Props {
		selectedLanguage?: string;
	}

	let { selectedLanguage = $bindable('English') }: Props = $props();

	const languages = [
		{ value: 'English', label: 'English' },
		{ value: 'Spanish', label: 'Spanish' },
		{ value: 'French', label: 'French' },
		{ value: 'German', label: 'German' },
		{ value: 'Italian', label: 'Italian' },
		{ value: 'Portuguese', label: 'Portuguese' },
		{ value: 'Chinese', label: 'Chinese' },
		{ value: 'Japanese', label: 'Japanese' },
		{ value: 'Polish', label: 'Polish' },
		{ value: 'Russian', label: 'Russian' },
		{ value: 'Arabic', label: 'Arabic' },
		{ value: 'Dutch', label: 'Dutch' }
	];
</script>

<div class="w-full">
	<Select bind:value={selectedLanguage} options={languages} class="w-full" />
</div>
