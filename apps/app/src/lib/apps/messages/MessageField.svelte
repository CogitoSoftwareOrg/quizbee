<script lang="ts">
	import { TextArea } from '@quizbee/ui-svelte-daisy';
	import type { QuizAttemptsResponse, QuizItemsResponse, QuizesResponse } from '$lib/pb';

	import type { Sender } from './types';
	import { messagesStore } from './stores/messages.svelte';

	type Props = {
		item: QuizItemsResponse;
		attempt: QuizAttemptsResponse;
		quiz: QuizesResponse;
		sender: Sender;
		inputText?: string;
		inputEl?: any;
		disabled?: boolean;
	};

	let {
		attempt,
		item,
		quiz,
		sender,
		inputEl = $bindable(),
		inputText = $bindable(''),
		disabled = false
	}: Props = $props();

	async function onkeydown(e: KeyboardEvent) {
		if (disabled) return;

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
	placeholder="Type your message…"
	rows={0}
></TextArea>
