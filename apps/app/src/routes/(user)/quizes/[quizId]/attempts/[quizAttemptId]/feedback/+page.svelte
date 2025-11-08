<script lang="ts">
	import { page } from '$app/state';
	import { Search, ChevronRight, ChevronLeft, Sparkles } from 'lucide-svelte';

	import { Button, Input } from '@quizbee/ui-svelte-daisy';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import ShareQuizButton from '$lib/apps/quizes/ShareQuizButton.svelte';
	import type { Decision } from '$lib/apps/quiz-attempts/types';

	import type { Answer } from '$lib/apps/quizes/types';
	import type { QuizExpand, QuizItemsResponse } from '$lib/pb';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	type Feedback = {
		overview?: string;
		problemTopics?: string[];
		uncoveredTopics?: string[];
	};

	const { data } = $props();

	const subscription = $derived(subscriptionStore.subscription);

	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);
	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	const correctCount = $derived(quizDecisions.filter((d) => d.correct).length);

	const pageQuiz = $derived(data.pageQuiz);
	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz) || pageQuiz);
	const quizItems = $derived(
		quizItemsStore.quizItemsMap.get(quiz?.id || '') ||
			(quiz?.expand as QuizExpand)?.quizItems_via_quiz ||
			[]
	);

	const feedback = $derived(quizAttempt?.feedback as Feedback | undefined);

	function findDecision(item: QuizItemsResponse): Decision | undefined {
		return quizDecisions.at(item.order);
	}

	let searchQuery = $state('');
	let filteredItems: QuizItemsResponse[] = $state([]);
	$effect(() => {
		const q = searchQuery.trim().toLowerCase();
		const items = (quizItems as unknown as QuizItemsResponse[]) || [];
		filteredItems = q
			? items.filter((item) => {
					const question = (item.question || '').toLowerCase();
					if (question.includes(q)) return true;
					const answers = item.answers as Answer[];
					return answers.some((a) => (a.content || '').toLowerCase().includes(q));
				})
			: items;
	});
</script>

<div
	class="relative mx-auto flex max-w-7xl flex-1 flex-col gap-6 p-1 pb-20 sm:h-full sm:flex-row sm:pb-1"
>
	{#if subscription?.tariff === 'free'}
		<section class="flex mt-3 sm:mt-0 flex-1 flex-col items-center justify-center gap-4 p-0 sm:p-4">
			<button
				onclick={() => {
					uiStore.setPaywallOpen(true);
				}}
				class="border-primary/30 hover:border-primary/50 group relative max-w-2xl cursor-pointer overflow-hidden rounded-2xl border p-6 shadow-xl transition-all hover:shadow-2xl sm:rounded-3xl sm:p-8 md:p-10"
			>
				<div class="relative z-10 flex flex-col gap-6">
					<div class="flex flex-col items-center gap-4 text-center">
						<div
							class="bg-primary/20 text-primary rounded-2xl p-4 transition-transform group-hover:scale-110 sm:p-5"
						>
							<Sparkles size={40} class="sm:size-12" />
						</div>
						<div class="space-y-3">
							<h3 class="text-base-content text-xl font-bold leading-tight sm:text-2xl md:text-3xl">
								AI-Powered Personalized Feedback
							</h3>
							<p class="text-base-content/70 text-sm leading-relaxed sm:text-base md:text-lg">
								Get detailed insights on your performance, identify problem topics, and discover
								uncovered areas. Our AI creates a personalized learning path just for you.
							</p>
						</div>
					</div>
					<div class="space-y-3">
						<div class="flex items-start gap-3">
							<div class="bg-success/20 text-success mt-1 rounded-lg p-1.5">
								<ChevronRight size={16} />
							</div>
							<p class="text-base-content/80 text-left text-sm sm:text-base">
								<strong>Performance Overview:</strong> Comprehensive analysis of your quiz results
							</p>
						</div>
						<div class="flex items-start gap-3">
							<div class="bg-error/20 text-error mt-1 rounded-lg p-1.5">
								<ChevronRight size={16} />
							</div>
							<p class="text-base-content/80 text-left text-sm sm:text-base">
								<strong>Problem Topics:</strong> Identify areas that need more attention
							</p>
						</div>
						<div class="flex items-start gap-3">
							<div class="bg-info/20 text-info mt-1 rounded-lg p-1.5">
								<ChevronRight size={16} />
							</div>
							<p class="text-base-content/80 text-left text-sm sm:text-base">
								<strong>Uncovered Topics:</strong> Discover what you haven't explored yet
							</p>
						</div>
					</div>
					<div class="btn btn-outline btn-primary btn-xl">
						Unlock AI Feedback
						<Sparkles size={20} />
					</div>
				</div>
				<div
					class="from-primary/10 pointer-events-none absolute inset-0 bg-gradient-to-br to-transparent opacity-50 transition-opacity group-hover:opacity-70"
				></div>
			</button>
		</section>
	{:else if !feedback?.overview}
		<section class="flex flex-1 flex-col items-center justify-center gap-4">
			<p class="loading loading-spinner loading-xl"></p>
			<p class="text-center font-semibold">We are giving your feedback...</p>
		</section>
	{:else if feedback?.overview}
		<section class="flex w-full flex-1 flex-col gap-6 px-3 sm:overflow-y-auto">
			<div>
				<Button color="neutral" style="ghost" href={`/home`} class="underline">
					<ChevronLeft /> Back to home
				</Button>
				<h2 class="text-center text-2xl font-bold leading-tight">Feedback</h2>
				<p class="mt-1 text-center text-sm opacity-70">
					Score: {correctCount} / {quizItems.length}
				</p>
			</div>

			<div>
				<div class="mt-4 space-y-2">
					<h3 class="text-lg font-semibold">Overview</h3>
					<p class="opacity-80">
						{feedback.overview}
					</p>
				</div>

				{#if feedback?.problemTopics?.length}
					<div class="mt-3">
						<p class="opacity-70">Problem topics:</p>
						<div class="flex flex-wrap gap-1">
							{#each feedback.problemTopics as topic}
								<span class="badge badge-soft badge-error">{topic}</span>
							{/each}
						</div>
					</div>
				{/if}

				{#if feedback?.uncoveredTopics?.length}
					<div class="mt-3">
						<p class="opacity-70">Uncovered topics:</p>
						<div class="flex flex-wrap gap-1">
							{#each feedback.uncoveredTopics as topic}
								<span class="badge badge-soft badge-info">{topic}</span>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</section>
	{/if}

	<section class="flex flex-1 flex-col gap-3 sm:min-h-0">
		<div class="flex items-center justify-between gap-4">
			{#if quiz}
				<h1 class="flex-1 text-center text-2xl font-bold leading-tight">{quiz?.title || 'Quiz'}</h1>
			{:else}
				<h1 class="flex-1 text-center text-2xl font-bold leading-tight">Loading...</h1>
			{/if}
			<Button
				color="neutral"
				style="ghost"
				href={`/quizes/${quiz?.id}`}
				class="hidden h-10 w-10 p-0 sm:flex"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="20"
					height="20"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<path d="M18 6 6 18" />
					<path d="m6 6 12 12" />
				</svg>
			</Button>
		</div>

		<Input
			class="w-full sm:shrink-0"
			placeholder="Search by questions and answers"
			value={searchQuery}
			oninput={(e) => {
				const t = e.target as HTMLInputElement;
				searchQuery = t.value;
			}}
		>
			{#snippet children()}
				<Search class="opacity-50" size={18} />
			{/snippet}
		</Input>

		{#if filteredItems.length === 0}
			<p class="py-6 text-center opacity-70">Nothing found</p>
		{:else if quiz && quizAttempt}
			<ul class="flex flex-1 flex-col gap-2 pr-1 sm:min-h-0 sm:overflow-y-auto">
				{#each filteredItems as item, index}
					{@const d = findDecision(item)}
					<li>
						<a
							class="hover:bg-base-200 border-base-300 group flex items-center justify-between gap-3 rounded-lg border p-3 no-underline shadow-sm transition hover:no-underline focus:no-underline"
							href={`/quizes/${quiz.id}/attempts/${quizAttempt.id}?order=${item.order}`}
						>
							<p class="text-base-content/80 group-hover:text-base-content flex-1 leading-relaxed">
								{index + 1}. {item.question}
							</p>
							<div class="flex items-center gap-3">
								{#if d}
									<span class={['badge', d.correct ? 'badge-success' : 'badge-error']}>
										{d.correct ? 'Correct' : 'Incorrect'}
									</span>
								{/if}
								<ChevronRight class="opacity-50 group-hover:opacity-80" size={18} />
							</div>
						</a>
					</li>
				{/each}
			</ul>
		{/if}

		{#if quiz}
			<div class="fixed bottom-12 left-0 right-0 z-10 p-4 sm:static sm:p-0">
				<ShareQuizButton quizId={quiz.id} quizTitle={quiz.title || 'Quiz'} block />
			</div>
		{/if}
	</section>
</div>
