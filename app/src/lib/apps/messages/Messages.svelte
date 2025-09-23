<script lang="ts">
	import { Bot, ChevronsDown } from 'lucide-svelte';
	import { fade } from 'svelte/transition';

	import Button from '$lib/ui/Button.svelte';

	import Message from './Message.svelte';
	import { scrollToBottom } from '$lib/actions/scroll-to-bottom';
	import type { MessagesResponse } from '$lib/pb';

	import type { Sender } from './types';

	interface Props {
		className: string;
		messages: MessagesResponse[];
		isWaitingAnswer: boolean;
		userSender: Sender;
		assistantSender: Sender;
	}

	const { className, messages, isWaitingAnswer, userSender, assistantSender }: Props = $props();

	let messagesContainer: HTMLElement | null = $state(null);
	let showScrollButton = $state(false);

	$effect(() => {
		if (messages.length > 0) setTimeout(() => scrollToBottom(messagesContainer), 100);
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
				<p class="text-base-content/70 text-lg font-medium">No messages yet, waiting...</p>
			</div>
		{:else}
			{#each messages as msg (msg)}
				{@const incoming = msg.role !== 'user'}
				{@const sender = msg.role === 'user' ? userSender : assistantSender}
				<Message {msg} {incoming} {sender} />
			{/each}
			{#if isWaitingAnswer}
				<div class="text-base-content/50 text-left text-sm">Generating...</div>
			{/if}
		{/if}

		{#if showScrollButton}
			<div class="absolute bottom-6 right-1/2 z-10 translate-x-1/2" transition:fade>
				<Button
					circle
					color="secondary"
					size="sm"
					onclick={() => scrollToBottom(messagesContainer)}
				>
					<ChevronsDown size={20} />
				</Button>
			</div>
		{/if}
	</div>
</div>
