<script lang="ts">
	import { page } from '$app/state';
	import { afterNavigate, goto } from '$app/navigation';

	import Button from '$lib/ui/Button.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import { pb } from '$lib/pb';
	import { computeApiUrl } from '$lib/api/compute-url';
	import Messages from '$lib/apps/messages/Messages.svelte';
	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte.js';
	import { userStore } from '$lib/apps/users/user.svelte';
	import type { Sender } from '$lib/apps/messages/types';
	import MessageField from '$lib/apps/messages/MessageField.svelte';
	import SendMessage from '$lib/apps/messages/SendMessage.svelte';
	import { ChevronLeft, ChevronRight, Info } from 'lucide-svelte';

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

	// MESSAGES
	const messages = $derived(
		messagesStore.messages.filter((m) => {
			const meta = m.metadata as { itemId: string };
			const itemId = meta?.itemId;
			return itemId === item?.id;
		})
	);

	let query = $state('');

	function gotoItem(idx: number) {
		const max = quizItems.length ? quizItems.length - 1 : 0;
		const clamped = Math.max(0, Math.min(idx, max));
		const u = new URL(page.url);
		u.searchParams.set('order', String(clamped));
		goto(u, { replaceState: clamped !== idx, keepFocus: true, noScroll: true });
	}

	// UI helpers
	function optionLabel(idx: number): string {
		return String.fromCharCode(65 + idx);
	}
</script>

<div class="flex h-full">
	<main class="relative flex-1">
		<div class="mx-auto h-full max-w-3xl p-4">
			<div class="flex items-start justify-between gap-4">
				<p class="text-2xl font-bold leading-snug">
					{item?.question || 'Loading...'}
				</p>
			</div>

			<ul class="relative mt-6 grid gap-3">
				<div
					class="pointer-events-none absolute -left-12 top-1/2 z-10 hidden -translate-y-1/2 md:block"
				>
					<Button
						class="pointer-events-auto"
						color="neutral"
						style="ghost"
						circle
						size="xl"
						onclick={() => {
							gotoItem(order - 1);
						}}
					>
						<ChevronLeft size={28} />
					</Button>
				</div>
				<div
					class="pointer-events-none absolute -right-12 top-1/2 z-10 hidden -translate-y-1/2 md:block"
				>
					<Button
						class="pointer-events-auto"
						color="neutral"
						style="ghost"
						circle
						size="xl"
						onclick={() => {
							if (!itemDecision) return;
							gotoItem(order + 1);
						}}
					>
						<ChevronRight size={28} />
					</Button>
				</div>
				{#each answers as answer, index}
					<li>
						<button
							class={[
								'border-base-300 bg-base-200 hover:border-primary/50 focus-visible:ring-primary/60 group w-full rounded-xl border text-left shadow-sm transition hover:shadow-md focus-visible:outline-none focus-visible:ring-2',
								itemDecision && answer.correct
									? 'ring-success/60 bg-success/10 border-success/40 ring-2'
									: '',
								itemDecision?.answerIndex === index && !answer.correct
									? 'ring-error/60 bg-error/10 border-error/40 ring-2'
									: '',
								!itemDecision ? 'hover:bg-base-300' : ''
							]}
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
							<div class="flex items-start gap-3 p-4">
								<span
									class={[
										'inline-flex h-8 w-8 items-center justify-center rounded-full border font-semibold',
										itemDecision?.answerIndex === index
											? 'border-primary text-primary'
											: 'border-base-300 text-base-content/70',
										itemDecision && answer.correct ? 'border-success text-success' : '',
										itemDecision?.answerIndex === index && !answer.correct
											? 'border-error text-error'
											: ''
									]}>{optionLabel(index)}</span
								>
								<div class="flex-1">
									<p class="leading-relaxed">{answer.content}</p>
								</div>
								{#if itemDecision}
									<div class="ml-2">
										{#if answer.correct}
											<span class="badge badge-success">Correct</span>
										{:else if itemDecision?.answerIndex === index}
											<span class="badge badge-error">Your pick</span>
										{/if}
									</div>
								{/if}
							</div>
						</button>
					</li>
				{/each}
			</ul>

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

			<div class="mt-6 flex justify-end gap-2">
				<Button color="neutral" style="soft">Manage Quiz</Button>
				<Button color="info" style="soft">Explain More</Button>
			</div>
		</div>
	</main>

	<aside class="h-full flex-1">
		{#if !itemDecision}
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
	</aside>
</div>
