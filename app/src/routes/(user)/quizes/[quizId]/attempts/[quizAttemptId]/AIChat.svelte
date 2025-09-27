<script lang="ts">
	import type { ClassValue } from 'svelte/elements';

	import type { Sender } from '$lib/apps/messages/types';
	import type { MessagesResponse, QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import Messages from '$lib/apps/messages/Messages.svelte';
	import MessageField from '$lib/apps/messages/MessageField.svelte';
	import SendMessage from '$lib/apps/messages/SendMessage.svelte';
	import Button from '$lib/ui/Button.svelte';
	import { X } from 'lucide-svelte';

	interface Props {
		class?: ClassValue;
		item: QuizItemsResponse | null;
		quizAttempt: QuizAttemptsResponse | null;
		itemDecision: Decision | null;
		messages: MessagesResponse[];
		userSender: Sender;
		assistantSender: Sender;
		open: boolean;
	}

	let {
		class: className,
		item,
		quizAttempt,
		itemDecision,
		messages,
		userSender,
		assistantSender,
		open = $bindable(false)
	}: Props = $props();

	let query = $state('');
</script>

<div class={['flex h-full flex-col overflow-hidden', className]}>
	<header class="border-base-200 flex items-center justify-between border-b px-3 py-2">
		<h2 class="text-sm font-semibold uppercase tracking-wide">AI Chat</h2>
		<Button style="ghost" circle color="neutral" onclick={() => (open = false)}>
			<X size={24} />
		</Button>
	</header>

	{#if !itemDecision || !item || !quizAttempt}
		<section class="flex flex-1 items-center justify-center px-6 text-center">
			<p class="text-lg font-semibold">
				You need to answer the question before interacting with the AI :3
			</p>
		</section>
	{:else}
		<section class="flex flex-1 flex-col overflow-hidden px-3 py-4">
			<div class="flex-1 overflow-y-auto pr-1">
				<Messages
					class="flex-1"
					{messages}
					{userSender}
					{assistantSender}
					quizAttemptId={quizAttempt.id}
					itemId={item.id}
				/>
			</div>
		</section>

		<footer class="border-base-200 border-t px-3 py-4">
			<MessageField bind:inputText={query} {item} attempt={quizAttempt} sender={userSender} />
			<div class="flex justify-end">
				<SendMessage {item} attempt={quizAttempt} sender={userSender} inputText={query} />
			</div>
		</footer>
	{/if}
</div>
