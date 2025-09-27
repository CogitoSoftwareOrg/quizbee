<script lang="ts">
	import Button from '$lib/ui/Button.svelte';
	import type { ClassValue } from 'svelte/elements';

	import { messagesStore } from './stores/messages.svelte';
	import type { Sender } from './types';

	type Props = {
		class?: ClassValue;
		color?:
			| 'primary'
			| 'secondary'
			| 'accent'
			| 'info'
			| 'success'
			| 'warning'
			| 'error'
			| 'neutral';
		style?: 'solid' | 'outline' | 'ghost' | 'link' | 'dash' | 'soft';
		sender: Sender;
		quizAttemptId: string;
		itemId: string;
	};

	const {
		sender,
		quizAttemptId,
		itemId,
		class: className,
		color = 'info',
		style = 'soft'
	}: Props = $props();
</script>

<Button
	onclick={async () => {
		if (!quizAttemptId || !itemId) return;
		messagesStore.sendMessage(sender, 'Explain this question', quizAttemptId, itemId);
	}}
	wide
	size="xl"
	class={className}
	{color}
	{style}
>
	Explain More
</Button>
