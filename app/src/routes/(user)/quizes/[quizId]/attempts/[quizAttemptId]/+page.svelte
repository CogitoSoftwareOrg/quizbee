<script lang="ts">
	import { page } from '$app/state';
	// explanations rendered in QuizAnswersList

	import Button from '$lib/ui/Button.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Answer } from '$lib/apps/quizes/types';
	import type { Sender } from '$lib/apps/messages/types';
	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';
	import { patchApi } from '$lib/api/call-api';

	import AIChat from './AIChat.svelte';
	import QuizItemsNavigation from './QuizItemsNavigation.svelte';
	import QuizAnswersList from './QuizAnswersList.svelte';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';

	const {} = $props();

	// QUIZ ATTEMPT
	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);

	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz));
	const quizItems = $derived(quizItemsStore.quizItemsMap.get(quiz?.id || '') || []);
	let itemDecision = $derived(quizDecisions.find((d) => d.itemId === item?.id) || null);

	const order = $derived.by(() => {
		const orderStr = page.url.searchParams.get('order');
		let order = orderStr ? parseInt(orderStr) : 0;
		const maxIdx = quizItems.length - 1;
		if (order < 0) order = 0;
		if (order > maxIdx) order = maxIdx;
		return order;
	});
	const item = $derived(quizItems.find((i) => i.order === order) || null);
	const answers = $derived((item?.answers as Answer[]) || []);

	// Messages
	const messages = $derived(
		messagesStore.messages.filter((m) => {
			const meta = m.metadata as { itemId: string };
			const itemId = meta?.itemId;
			return itemId === item?.id;
		})
	);

	const userSender = $derived(userStore.sender);
	const assistantSender: Sender = $derived({
		role: 'ai',
		id: 'ai',
		avatar: '',
		name: 'Assistant'
	});

	let chatOpen = $state(false);
	const mainColumnWidth = $derived(chatOpen ? '50%' : '100%');
	const chatColumnWidth = $derived(chatOpen ? '50%' : '0%');
</script>

<div class="flex h-full overflow-hidden">
	<main
		class="border-base-200 relative h-full min-w-0 flex-shrink-0 border-r transition-[width] duration-300 ease-out"
		style:width={mainColumnWidth}
	>
		{#if !chatOpen}
			<div class="absolute -right-3 top-1/2 -translate-y-1/2">
				<button
					class="bg-primary flex-1 cursor-pointer rounded-2xl p-2 text-center text-2xl font-semibold"
					onclick={() => (chatOpen = !chatOpen)}
				>
					<span
						class="block select-none whitespace-nowrap tracking-widest text-black"
						style="writing-mode: vertical-rl; transform: rotate(180deg);"
					>
						AI Chat
					</span>
				</button>
			</div>
		{/if}

		<div class="relative mx-auto flex h-full max-w-3xl flex-col p-2">
			<div class="flex items-start justify-between gap-4 px-3">
				<p class="text-center text-2xl font-bold leading-snug">
					{item?.question || 'Loading...'}
				</p>
			</div>

			{#if item && quiz && quizAttempt}
				<QuizItemsNavigation {quizAttempt} {quizItems} {order} {itemDecision} />
			{/if}

			{#if item && quiz && quizAttempt}
				<QuizAnswersList
					class="relative mt-6 flex-1 overflow-y-auto"
					{answers}
					{quizItems}
					{quizDecisions}
					{quiz}
					{item}
					{quizAttempt}
					bind:itemDecision
				/>
			{/if}

			{#if itemDecision}
				<div class="mt-6 flex gap-2">
					<Button
						onclick={async () => {
							const result = await patchApi(`quizes/${quiz?.id}`, {
								attempt_id: quizAttemptId,
								limit: 50 // for now just gurantee total number of questions
							});

							console.log('Quiz settings updated:', result);
						}}
						class="flex-1"
						color="neutral"
						style="soft">Manage Quiz</Button
					>
				</div>
			{/if}
		</div>
	</main>

	<div
		class="h-full min-w-0 flex-shrink-0 overflow-hidden transition-[width] duration-300 ease-out"
		style:pointer-events={!chatOpen ? 'none' : 'auto'}
		style:width={chatColumnWidth}
	>
		<AIChat
			class="flex h-full flex-col px-2"
			{item}
			{quizAttempt}
			{itemDecision}
			{messages}
			{userSender}
			{assistantSender}
			bind:open={chatOpen}
		/>
	</div>
</div>
