<script lang="ts">
	import { page } from '$app/state';
	import { Info } from 'lucide-svelte';

	import Button from '$lib/ui/Button.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Answer } from '$lib/apps/quizes/types';

	import AIChat from './AIChat.svelte';
	import QuizItemsNavigation from './QuizItemsNavigation.svelte';
	import QuizAnswersList from './QuizAnswersList.svelte';
	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte';
	import type { Sender } from '$lib/apps/messages/types';
	import { userStore } from '$lib/apps/users/user.svelte';

	const {} = $props();

	// QUIZ ATTEMPT
	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);

	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz));
	const quizItems = $derived(
		quiz?.expand.quizItems_via_quiz?.toSorted((a, b) => a.order - b.order) || []
	);
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
</script>

<div class="flex h-full">
	<main class="border-base-200 relative flex-1 border-r">
		<div class="mx-auto flex h-full max-w-3xl flex-col p-2">
			<div class="flex items-start justify-between gap-4">
				<p class="text-2xl font-bold leading-snug">
					{item?.question || 'Loading...'}
				</p>
			</div>

			<QuizItemsNavigation {quizItems} {order} {itemDecision} />

			{#if item && quiz && quizAttempt}
				<QuizAnswersList
					class="relative mt-6 flex-1"
					{answers}
					{quizItems}
					{quizDecisions}
					{quiz}
					{item}
					{quizAttempt}
					{itemDecision}
				/>
			{/if}

			{#if itemDecision}
				{#each answers as answer, index}
					{#if answers[index]?.explanation}
						<div
							class={[
								'mt-3 rounded-xl border p-4',
								index === itemDecision?.answerIndex
									? 'border-info/50 bg-info/10'
									: 'border-base-300 bg-base-200'
							]}
						>
							<div class="flex items-start gap-2">
								<Info class="mt-0.5" size={18} />
								<div class="flex-1">
									<p class="text-sm opacity-80">{answer.explanation}</p>
								</div>
							</div>
						</div>
					{/if}
				{/each}
			{/if}

			{#if itemDecision}
				<div class="mt-6 flex justify-end gap-2">
					<Button color="neutral" style="soft">Manage Quiz</Button>
					<Button color="info" style="soft">Explain More</Button>
				</div>
			{/if}
		</div>
	</main>

	<AIChat
		class="h-full flex-1 px-2"
		{item}
		{quizAttempt}
		{itemDecision}
		{messages}
		{userSender}
		{assistantSender}
	/>
</div>
