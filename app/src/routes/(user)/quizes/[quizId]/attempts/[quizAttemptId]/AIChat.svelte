<script lang="ts">
	import type { ClassValue } from 'svelte/elements';

	import type { Sender } from '$lib/apps/messages/types';
	import type { MessagesResponse, QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import Messages from '$lib/apps/messages/Messages.svelte';
	import MessageField from '$lib/apps/messages/MessageField.svelte';
	import SendMessage from '$lib/apps/messages/SendMessage.svelte';

	interface Props {
		class?: ClassValue;
		item: QuizItemsResponse | null;
		quizAttempt: QuizAttemptsResponse | null;
		itemDecision: Decision | null;
		messages: MessagesResponse[];
		userSender: Sender;
		assistantSender: Sender;
	}

	let {
		class: className,
		item,
		quizAttempt,
		itemDecision,
		messages,
		userSender,
		assistantSender
	}: Props = $props();

	let query = $state('');
</script>

<div class={className}>
	{#if !itemDecision || !item || !quizAttempt}
		<div class="flex h-full items-center justify-center">
			<p class="mx-12 px-6 text-center text-2xl font-bold">
				You need to answer the question before interacting with the AI :3
			</p>
		</div>
	{:else}
		<div class="flex h-full flex-col">
			<div class="w-full flex-1 overflow-hidden">
				<Messages class="flex-1" {messages} {userSender} {assistantSender} />
			</div>

			{#if item && quizAttempt}
				<footer>
					<MessageField bind:inputText={query} {item} attempt={quizAttempt} sender={userSender} />
					<div class="flex justify-end">
						<SendMessage {item} attempt={quizAttempt} sender={userSender} inputText={query} />
					</div>
				</footer>
			{/if}
		</div>
	{/if}
</div>
