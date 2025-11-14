<script lang="ts">
	import { TextArea } from '@quizbee/ui-svelte-daisy';
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
		sender: Sender;
		messages: MessagesResponse[];
		inputText?: string;
		inputEl?: any;
		disabled?: boolean;
	};

	let {
		attempt,
		item,
		quiz,
		sender,
		messages,
		inputEl = $bindable(),
		inputText = $bindable(''),
		disabled = false
	}: Props = $props();

	const canWrite = $derived.by(() => {
		if (disabled) return false;
		return true;
	});

	const canSend = $derived.by(() => {
		if (messages.length === 0) return true;
		if (!inputText || inputText.trim() === '') return false;
		const lastMessage = messages[messages.length - 1];
		return lastMessage.role === 'ai' && lastMessage.status === 'final';
	});

	async function onkeydown(e: KeyboardEvent) {
		if (!canSend) return;

		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();

			// SEND MESSAGE
			const text = inputText;
			inputText = '';
			await messagesStore.sendMessage(sender, text, attempt.id, quiz.id, item.id);

			if (inputEl && 'style' in inputEl) inputEl.style.height = 'auto';
		}
	}
</script>

<TextArea
	class="mb-2 max-h-32 w-full resize-none overflow-y-auto px-5"
	bind:el={inputEl}
	bind:value={inputText}
	grow
	{onkeydown}
	disabled={!canWrite}
	placeholder="Type your message…"
	rows={0}
></TextArea>
