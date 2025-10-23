<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import { MessageCirclePlus } from 'lucide-svelte';

	import { Button } from '@cogisoft/ui-svelte-daisy';

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
		chatOpen?: boolean;
	};

	let {
		sender,
		quizAttemptId,
		itemId,
		class: className,
		color = 'neutral',
		style = 'outline',
		chatOpen = $bindable(false)
	}: Props = $props();

	const messages = $derived(
		messagesStore.messages.filter(
			(m) => m.quizAttempt === quizAttemptId && (m.metadata as any)?.itemId === itemId
		)
	);
</script>

<Button
	disabled={messages.length !== 0}
	onclick={async () => {
		if (!quizAttemptId || !itemId) return;
		chatOpen = true;
		messagesStore.sendMessage(sender, 'Explain this question', quizAttemptId, itemId);
	}}
	size="lg"
	class={`dark:text-base-content/90 min-w-40 ${className || ''}`}
	{color}
	{style}
>
	<MessageCirclePlus class="mb-0.5" size={20} />

	Explain
</Button>
