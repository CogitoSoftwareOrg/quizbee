<script lang="ts">
	import { ChevronsRight } from 'lucide-svelte';

	import { Button } from '@quizbee/ui-svelte-daisy';

	import type {
		MessagesResponse,
		QuizAttemptsResponse,
		QuizItemsResponse,
		QuizesResponse
	} from '$lib/pb';

	import type { Sender } from './types';
	import { messagesStore } from './stores/messages.svelte';

	type Props = {
		item: QuizItemsResponse;
		attempt: QuizAttemptsResponse;
		quiz: QuizesResponse;
		messages: MessagesResponse[];
		inputText?: string;
		inputEl?: HTMLTextAreaElement | null;
		class?: string;
		disabled?: boolean;
		sender: Sender;
	};

	let {
		item,
		attempt,
		quiz,
		messages,
		inputEl,
		class: className,
		inputText = '',
		disabled = false,
		sender
	}: Props = $props();

	const canSend = $derived.by(() => {
		if (disabled) return false;
		if (!inputText || inputText.trim() === '') return false;

		if (messages.length === 0) return true; // Allow first message

		// Check if last message is AI with final status
		const lastMessage = messages[messages.length - 1];
		return lastMessage.role === 'ai' && lastMessage.status === 'final';
	});

	async function send() {
		if (!canSend) return;

		// SEND MESSAGE
		const text = inputText;
		await messagesStore.sendMessage(sender, text, attempt.id, quiz.id, item.id);

		if (inputEl) inputEl.style.height = 'auto';
		// Note: inputText is cleared in MessageField via bind:inputText
	}
</script>

<div class={className}>
	<Button disabled={!canSend} onclick={send}>
		<ChevronsRight size={32} />
	</Button>
</div>
