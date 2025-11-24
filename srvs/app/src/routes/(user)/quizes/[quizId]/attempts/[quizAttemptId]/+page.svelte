<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import posthog from 'posthog-js';

	import { Button } from '@quizbee/ui-svelte-daisy';
	import type { QuizExpand } from '@quizbee/pb-types';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Answer } from '$lib/apps/quizes/types';
	import type { Sender } from '$lib/apps/messages/types';
	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';

	import AIChat from './AIChat.svelte';
	import QuizItemsNavigation from './QuizItemsNavigation.svelte';
	import QuizAnswersList from './QuizAnswersList.svelte';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
	import ManageQuiz from './ManageQuiz.svelte';
	import SwipeableContent from './SwipeableContent.svelte';
	import MobileAIChat from './MobileAIChat.svelte';
	import { X } from 'lucide-svelte';
	import { patchApi } from '$lib/api/call-api';
	import QuizItemSourceTooltip from '$lib/apps/quizes/QuizItemSourceTooltip.svelte';

	const { data } = $props();

	// QUIZ ATTEMPT
	const user = $derived(userStore.user);
	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);

	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	// Stable itemDecision - preserve optimistic updates, only sync when server data differs
	let itemDecision = $state<Decision | null>(null);
	let lastOrder = $state<number | null>(null);

	$effect(() => {
		const currentOrder = item?.order ?? null;

		// Reset itemDecision when navigating to a different item
		if (currentOrder !== lastOrder) {
			lastOrder = currentOrder;
			itemDecision = null;
		}

		// Load decision from server if it exists
		const foundDecision = quizDecisions.at(currentOrder ?? 0) || null;
		if (foundDecision) {
			itemDecision = foundDecision;
		}
	});

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
	const hint = $derived((item?.hint as string) || '');

	// Messages
	const messages = $derived(
		messagesStore.messages.filter((m) => {
			const meta = m.metadata as { item_id: string };
			const itemId = meta?.item_id;
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

	// we need those vatiables for correct 1-time logging
	let firstQuestionLogged = $state(false);
	let fifthQuestionLogged = $state(false);

	$effect(() => {
		if (!quizAttempt) return;

		messagesStore.load(quizAttempt.id).then(() => {
			messagesStore.subscribe(quizAttempt.id);
		});
		return () => {
			messagesStore.unsubscribe();
		};
	});

	$effect(() => {
		const firstDecision = quizDecisions.at(0);
		if (firstDecision && quiz?.id && quizAttempt?.id && !firstQuestionLogged) {
			firstQuestionLogged = true;
			posthog.capture('quiz_first_question_answered', {
				quizId: quiz.id,
				attemptId: quizAttempt.id
			});
		}
	});

	$effect(() => {
		const fifthDecision = quizDecisions.at(4);
		if (fifthDecision && quiz?.id && quizAttempt?.id && !fifthQuestionLogged) {
			fifthQuestionLogged = true;
			posthog.capture('quiz_fifth_question_answered', {
				quizId: quiz.id,
				attemptId: quizAttempt.id
			});
		}
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

	async function handleSwipeRight() {
		if (!itemDecision || !quiz || !quizAttempt || !item) return;
		if (order + 1 === quizItems.length) {
			gotoFinal();
		} else {
			gotoItem(order + 1);
		}

		if (quiz.author === user?.id && quizDecisions.length === item?.order + 1) {
			await patchApi(`quizes/${quiz.id}`, {
				attempt_id: quizAttempt.id,
				mode: 'continue'
			});
		}
	}

	const canSwipeLeft = $derived(order > 0);
	const canSwipeRight = $derived(!!itemDecision);

	const currentItem = $derived(quizItems.find((qi) => qi.order === order));
	const itemToAnswer = $derived(quizItems.find((qi) => !quizDecisions.at(qi.order)));
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
	<header class="flex items-center justify-between px-2 py-1">
		<ul class="hidden flex-1 flex-wrap items-center gap-1 sm:flex">
			{#each quizItems as quizItem, index}
				{@const decision = quizDecisions.at(quizItem.order)}

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

		<ul class="flex flex-1 flex-wrap items-center gap-1.5 sm:hidden">
			{#each quizItems as quizItem}
				{@const decision = quizDecisions.at(quizItem.order)}
				{@const isDisabled = !decision && quizItem.order > (itemToAnswer?.order || 0)}
				{@const isCurrent = currentItem?.id === quizItem.id}

				<li>
					<div
						class={[
							'block rounded-full transition-all',
							isCurrent ? 'size-2.5' : 'size-1.5',
							decision?.correct
								? 'bg-success'
								: decision && !decision?.correct
									? 'bg-error'
									: 'bg-neutral/30',
							isDisabled ? 'opacity-40' : ''
						].join(' ')}
						aria-label={`Question ${quizItem.order + 1}`}
					></div>
				</li>
			{/each}
		</ul>

		<div class="flex items-center gap-1 sm:hidden">
			<Button href="/quizes" color="neutral" style="ghost" circle>
				<X size={24} />
			</Button>
		</div>
	</header>

	<div class="flex flex-1 overflow-hidden">
		<div class="relative flex h-full min-w-0 flex-1">
			<!-- Main column -->
			<main
				class="h-full min-w-0 flex-1 overflow-x-hidden border-r border-base-200 transition-[width] duration-300 ease-out"
				style:width={mainColumnWidth}
			>
				<SwipeableContent
					{canSwipeLeft}
					{canSwipeRight}
					onSwipeLeft={handleSwipeLeft}
					onSwipeRight={handleSwipeRight}
					class="relative h-full overflow-x-hidden pb-2"
				>
					<div class="mx-auto flex h-full max-w-3xl min-w-0 flex-col py-2">
						<div class="flex min-w-0 items-start justify-between gap-4 px-3">
							<p
								class="wrap-break-words min-w-0 flex-1 text-center text-2xl leading-snug font-bold"
							>
								{@html item?.question}
							</p>
							<QuizItemSourceTooltip usedChunks={item?.usedChunks} {itemDecision} />
						</div>

						{#if item && quiz && quizAttempt}
							<QuizAnswersList
								class="relative mt-6 flex-1 overflow-y-auto md:text-lg"
								{answers}
								{quizItems}
								{quizDecisions}
								{quiz}
								{item}
								{quizAttempt}
								bind:itemDecision
								{hint}
							/>
						{/if}

						{#if quiz?.status !== 'final' && user?.id === quiz?.author && lastFinalItem?.id === item?.id && item && !item?.managed && itemDecision && quiz && quizAttempt}
							<ManageQuiz {item} {quiz} {quizAttempt} />
						{/if}

						{#if item && quiz && quizAttempt}
							<QuizItemsNavigation
								{quizAttempt}
								{quiz}
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
					</div>
				</SwipeableContent>
			</main>

			{#if !chatOpen}
				<div class="absolute top-1/2 -right-3 hidden -translate-y-1/2 sm:block">
					<button
						class="flex-1 cursor-pointer rounded-2xl bg-primary p-2 text-center text-2xl font-semibold"
						onclick={() => (chatOpen = !chatOpen)}
					>
						<span
							class="block tracking-widest whitespace-nowrap text-black select-none"
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
				{quiz}
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
	{quiz}
	{item}
	{quizAttempt}
	{itemDecision}
	{messages}
	{userSender}
	{assistantSender}
	bind:open={chatOpen}
/>
