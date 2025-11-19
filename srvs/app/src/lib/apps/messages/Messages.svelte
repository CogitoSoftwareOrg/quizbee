<script lang="ts">
	import { ChevronsDown } from 'lucide-svelte';
	import type { ClassValue } from 'svelte/elements';
	import { fade } from 'svelte/transition';

	import { Button, scrollToBottom } from '@quizbee/ui-svelte-daisy';

	import type { MessagesResponse, QuizesResponse } from '$lib/pb';

	import type { Sender } from './types';
	import Message from './Message.svelte';
	import ExplainMore from './ExplainMore.svelte';

	interface Props {
		quizAttemptId: string;
		itemId: string;
		messages: MessagesResponse[];
		quiz: QuizesResponse;
		userSender: Sender;
		assistantSender: Sender;
		class?: ClassValue;
	}

	const {
		class: className,
		messages,
		userSender,
		assistantSender,
		quizAttemptId,
		itemId,
		quiz
	}: Props = $props();

	let messagesContainer: HTMLElement | null = $state(null);
	let showScrollButton = $state(false);

	let lastLength = 0;
	$effect(() => {
		if (messages.length > 0) {
			if (messages.length > lastLength) setTimeout(() => scrollToBottom(messagesContainer), 100);
			lastLength = messages.length;
		}
	});

	function onscroll() {
		if (!messagesContainer) return;
		const { scrollTop, clientHeight, scrollHeight } = messagesContainer;
		const atBottom = scrollTop + clientHeight >= scrollHeight - 5;
		showScrollButton = !atBottom;
	}
</script>

<div class={[className, 'bg-base-100 relative h-full']}>
	<div
		bind:this={messagesContainer}
		{onscroll}
		class={['h-full space-y-2 overflow-y-auto overscroll-contain px-2 py-1']}
	>
		{#if messages.length === 0}
			<div class="flex h-full flex-col items-center justify-center text-center">
				<div class="mb-4 text-6xl">💬</div>
				<p class="text-base-content/70 mb-3 text-lg font-medium">No messages yet, waiting...</p>
				<ExplainMore sender={userSender} {quizAttemptId} {itemId} {quiz} />
			</div>
		{:else}
			{#each messages as msg (msg)}
				{@const incoming = msg.role !== 'user'}
				{@const sender = msg.role === 'user' ? userSender : assistantSender}
				<Message {msg} {incoming} {sender} showHeader={msg.role === 'user'} />
			{/each}
		{/if}

		{#if showScrollButton}
			<div class="absolute bottom-2 right-1/2 z-10 translate-x-1/2" transition:fade>
				<Button
					circle
					color="neutral"
					size="xs"
					class="opacity-40 hover:opacity-70"
					onclick={() => scrollToBottom(messagesContainer)}
				>
					<ChevronsDown size={16} />
				</Button>
			</div>
		{/if}
	</div>
</div>
