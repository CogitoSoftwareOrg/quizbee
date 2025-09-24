<script lang="ts">
	import { page } from '$app/state';
	import { afterNavigate, goto } from '$app/navigation';

	import Button from '$lib/ui/Button.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import { pb } from '$lib/pb';
	import { computeApiUrl } from '$lib/api/compute-url';
	import Messages from '$lib/apps/messages/Messages.svelte';
	import { messagesStore } from '$lib/apps/messages/messages.svelte.js';
	import { userStore } from '$lib/apps/users/user.svelte';
	import type { Sender } from '$lib/apps/messages/types';
	import { Bot } from 'lucide-svelte';

	type Answer = {
		content: string;
		correct: boolean;
		explanation: string;
	};
	type Decision = {
		itemId: string;
		answerIndex: number;
		correct: boolean;
	};

	const {} = $props();

	// MESSAGES
	const messages = $derived(messagesStore.messages);
	const userSender = $derived(userStore.sender);
	const assistantSender: Sender = $derived({
		role: 'ai',
		id: 'ai',
		avatar: '',
		name: 'Assistant'
	});

	// QUIZ ATTEMPT
	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId)
	);

	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz));
	const quizItems = $derived(
		quiz?.expand.quizItems_via_quiz?.toSorted((a, b) => a.order - b.order) || []
	);
	let itemDecision = $derived(quizDecisions.find((d) => d.itemId === item?.id) || null);

	const readyItemsWithoutDecisions = $derived(
		quizItems.filter((i) => !quizDecisions.some((d) => d.itemId === i.id) && i.status === 'final')
	);

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

	function gotoItem(idx: number) {
		const max = quizItems.length ? quizItems.length - 1 : 0;
		const clamped = Math.max(0, Math.min(idx, max));
		const u = new URL(page.url);
		u.searchParams.set('order', String(clamped));
		goto(u, { replaceState: clamped !== idx, keepFocus: true, noScroll: true });
	}
</script>

<div class="flex h-full">
	<main class="flex-1">
		<p class="text-lg font-bold">
			{item?.question || 'Loading...'}
		</p>
		<ul class="space-y-2">
			{#each answers as answer, index}
				<li
					class={[
						'w-fit',
						itemDecision && answer.correct ? 'bg-primary/50' : '',
						itemDecision?.answerIndex === index && !answer.correct ? 'bg-error/50' : ''
					]}
				>
					<Button
						color="neutral"
						style="outline"
						onclick={async () => {
							if (itemDecision) return;
							itemDecision = {
								itemId: item!.id,
								answerIndex: index,
								correct: answer.correct
							};
							if (readyItemsWithoutDecisions.length <= 2) {
								const r2 = await fetch(`${computeApiUrl()}/quizes/${quiz!.id}`, {
									method: 'PATCH',
									body: JSON.stringify({
										limit: 2
									}),
									headers: {
										'Content-Type': 'application/json'
									},
									credentials: 'include'
								});
								if (!r2.ok) {
									console.error(await r2.text());
									return;
								}
								console.log(await r2.json());
							}

							await pb!.collection('quizAttempts').update(quizAttemptId!, {
								choices: [...quizDecisions, itemDecision]
							});
						}}
					>
						<p></p>
						{answer.content}
					</Button>
					{#if itemDecision}
						<p class="text-center text-sm text-gray-500">{answer.explanation}</p>
					{/if}
				</li>
			{/each}
		</ul>

		{#if itemDecision}
			<div>
				<button
					class="btn"
					onclick={() => {
						gotoItem(order - 1);
					}}>Previous</button
				>
				<button
					class="btn"
					onclick={() => {
						gotoItem(order + 1);
					}}>Next</button
				>
			</div>
		{/if}
	</main>

	<aside class="h-full flex-1">
		{#if !itemDecision}
			<div class="flex h-full items-center justify-center">
				<p class="mx-12 px-6 text-center text-2xl font-bold">
					You need to answer the question before interacting with the AI :3
				</p>
			</div>
		{:else}
			<div>
				<Messages {messages} {userSender} {assistantSender} />
				
			</div>
		{/if}
	</aside>
</div>
