<script lang="ts">
	import type { Snippet } from 'svelte';

	interface Props {
		open: boolean;
		children: Snippet;
		sidebar: Snippet;
		openText: string;
	}

	const { open = $bindable(), children, sidebar }: Props = $props();
</script>

{#if open}
	<div></div>
{:else}{/if}
