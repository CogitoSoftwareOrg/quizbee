<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	import { Button } from '@cogisoft/ui-svelte-daisy';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Answer } from '$lib/apps/quizes/types';
	import type { Sender } from '$lib/apps/messages/types';
	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';
	import type { QuizExpand } from '$lib/pb';

	import AIChat from './AIChat.svelte';
	import QuizItemsNavigation from './QuizItemsNavigation.svelte';
	import QuizAnswersList from './QuizAnswersList.svelte';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
	import ManageQuiz from './ManageQuiz.svelte';
	import SwipeableContent from './SwipeableContent.svelte';
	import MobileAIChat from './MobileAIChat.svelte';

	const { data } = $props();

	// QUIZ ATTEMPT
	const user = $derived(userStore.user);
	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);

	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);
	let itemDecision = $derived(quizDecisions.find((d) => d.itemId === item?.id) || null);

	const pageQuiz = $derived(data?.pageQuiz?.id === quizAttempt?.quiz ? data.pageQuiz : null);
	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz) || pageQuiz);
	const quizItems = $derived(
		quizItemsStore.quizItemsMap.get(quiz?.id || '') ||
			(quiz?.expand as QuizExpand)?.quizItems_via_quiz ||
			[]
	);
	const lastFinalItem = $derived(quizItems.filter((i) => i.status === 'final').at(-1));

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

	$effect(() => {
		if (!quizAttempt) return;

		messagesStore.load(quizAttempt.id).then(() => {
			messagesStore.subscribe(quizAttempt.id);
		});
		return () => {
			messagesStore.unsubscribe();
		};
	});

	// Swipe navigation helpers
	function gotoItem(idx: number) {
		const max = quizItems.length ? quizItems.length - 1 : 0;
		const clamped = Math.max(0, Math.min(idx, max));

		// относительный href БЕЗ pathname — привяжется к текущему пути
		const href = `?order=${clamped}`;

		goto(href, {
			replaceState: clamped !== idx,
			keepFocus: true,
			noScroll: true
		});
	}

	function gotoFinal() {
		const u = new URL(page.url);
		goto(`${u.pathname}/feedback`, { replaceState: false, keepFocus: true, noScroll: true });
	}

	function handleSwipeLeft() {
		if (order > 0) {
			gotoItem(order - 1);
		}
	}

	function handleSwipeRight() {
		if (itemDecision) {
			if (order + 1 === quizItems.length) {
				gotoFinal();
			} else {
				gotoItem(order + 1);
			}
		}
	}

	const canSwipeLeft = $derived(order > 0);
	const canSwipeRight = $derived(!!itemDecision);

	const currentItem = $derived(quizItems.find((qi) => qi.order === order));
	const itemToAnswer = $derived(
		quizItems.find((qi) => !quizDecisions.some((d) => d.itemId === qi.id))
	);
	const showManage = $derived(
		Boolean(
			quiz?.status !== 'final' &&
			user?.id === quiz?.author &&
			lastFinalItem?.id === item?.id &&
			item &&
			!item?.managed &&
			itemDecision &&
			quiz &&
			quizAttempt
		)
	);
</script>

<div class="flex h-full flex-col">
	<header class="px-4 py-2 sm:block">
		<ul class="hidden flex-1 flex-wrap items-center gap-1 sm:flex">
			{#each quizItems as quizItem, index}
				{@const decision = quizDecisions.find((d) => d.itemId === quizItem.id)}

				<li>
					<Button
						disabled={!decision && quizItem.order > (itemToAnswer?.order || 0)}
						color={decision?.correct
							? 'success'
							: decision && !decision?.correct
								? 'error'
								: 'neutral'}
						href={`/quizes/${quiz?.id}/attempts/${quizAttempt?.id}?order=${quizItem.order}`}
						style={currentItem?.id === quizItem.id ? 'solid' : 'outline'}
						size="xs"
						circle
					>
						{index + 1}
					</Button>
				</li>
			{/each}
		</ul>
	</header>

	<div class="flex flex-1 overflow-hidden">
		<div class="relative flex h-full min-w-0 flex-1">
			<!-- Main column -->
			<main
				class="border-base-200 h-full min-w-0 flex-1 overflow-x-hidden border-r transition-[width] duration-300 ease-out"
				style:width={mainColumnWidth}
			>
				<SwipeableContent
					{canSwipeLeft}
					{canSwipeRight}
					onSwipeLeft={handleSwipeLeft}
					onSwipeRight={handleSwipeRight}
					class="relative h-full overflow-x-hidden"
				>
					<div class="mx-auto flex h-full min-w-0 max-w-3xl flex-col py-2">
						<div class="flex min-w-0 items-start justify-between gap-4 px-3">
							<p
								class="wrap-break-words min-w-0 flex-1 text-center text-2xl font-bold leading-snug"
							>
								{@html item?.question}
							</p>
						</div>

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

						{#if item && quiz && quizAttempt}
							<QuizItemsNavigation
								{quizAttempt}
								{quizItems}
								{order}
								{itemDecision}
								bind:chatOpen
								{userSender}
								itemId={item.id}
								onPrevious={handleSwipeLeft}
								onNext={handleSwipeRight}
							/>
						{/if}

						{#if quiz?.status !== 'final' && user?.id === quiz?.author && lastFinalItem?.id === item?.id && item && !item?.managed && itemDecision && quiz && quizAttempt}
							<ManageQuiz {item} {quiz} {quizAttempt} />
						{:else if item && quiz && quizAttempt}   <!-- invisible placeholder to maintain layout -->
							<div class="mt-6 flex gap-2" aria-hidden="true">
								<Button
									class="invisible pointer-events-none"
									style="soft"
								>
									Adjust Quiz
								</Button>
							</div>
						{/if}
					</div>
				</SwipeableContent>
			</main>

			{#if !chatOpen}
				<div class="absolute -right-3 top-1/2 hidden -translate-y-1/2 sm:block">
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
		</div>

		<!-- Desktop AI Chat -->
		<div
			class="hidden h-full min-w-0 shrink-0 overflow-hidden transition-[width] duration-300 ease-out sm:block"
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
</div>
<!-- Mobile AI Chat (bottom sheet) -->
<MobileAIChat
	{item}
	{quizAttempt}
	{itemDecision}
	{messages}
	{userSender}
	{assistantSender}
	bind:open={chatOpen}
/>
