<script lang="ts">
	import { ChevronsRight } from 'lucide-svelte';

	import { Button } from '@cogisoft/ui-svelte-daisy';

	import type { QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';

	import type { Sender } from './types';
	import { messagesStore } from './stores/messages.svelte';

	type Props = {
		item: QuizItemsResponse;
		attempt: QuizAttemptsResponse;
		inputText?: string;
		inputEl?: HTMLTextAreaElement | null;
		class?: string;
		disabled?: boolean;
		sender: Sender;
	};

	let {
		item,
		attempt,
		inputEl,
		class: className,
		inputText = $bindable(''),
		disabled = false,
		sender
	}: Props = $props();

	async function send() {
		if (disabled) return;

		// SEND MESSAGE
		const text = inputText;
		inputText = '';
		await messagesStore.sendMessage(sender, text, attempt.id, item.id);

		if (inputEl) inputEl.style.height = 'auto';
	}
</script>

<div class={className}>
	<Button {disabled} onclick={send}>
		<ChevronsRight size={32} />
	</Button>
</div>
