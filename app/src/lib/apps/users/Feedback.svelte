<script lang="ts">
	import { MessageCircleHeart } from 'lucide-svelte';
	import type { ClassValue } from 'svelte/elements';

	import { uiStore } from './ui.svelte';

	interface Props {
		class?: ClassValue;
		expanded?: boolean;
	}
	let { class: className, expanded = false }: Props = $props();
</script>

{#if expanded}
	<button
		class={[
			'hover:bg-base-300 border-base-300 flex w-full cursor-pointer items-center gap-3 rounded-lg border px-2 py-1 transition-colors',
			className
		]}
		onclick={() => uiStore.setFeedbackModalOpen(true)}
	>
		<MessageCircleHeart class="size-7 shrink-0" />
		<span class="text-base-content text-nowrap text-sm font-medium">Feedback & Support</span>
	</button>
{:else}
	<button class={['cursor-pointer', className]} onclick={() => uiStore.setFeedbackModalOpen(true)}>
		<MessageCircleHeart class="size-7" />
	</button>
{/if}
