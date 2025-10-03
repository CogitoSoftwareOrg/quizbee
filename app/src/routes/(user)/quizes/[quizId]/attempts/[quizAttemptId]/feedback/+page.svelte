<script lang="ts">
	import { page } from '$app/state';
	import { Search, ChevronRight, ChevronLeft } from 'lucide-svelte';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import Button from '$lib/ui/Button.svelte';
	import Input from '$lib/ui/Input.svelte';
	import type { Answer } from '$lib/apps/quizes/types';
	import type { QuizItemsResponse } from '$lib/pb';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';

	type Feedback = {
		quiz_title: string;
		overview: string;
		problem_topics: string[];
		uncovered_topics: string[];
	};

	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);
	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	const correctCount = $derived(quizDecisions.filter((d) => d.correct).length);

	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz));
	const quizItems = $derived(quizItemsStore.quizItemsMap.get(quiz?.id || '') || []);

	const feedback = $derived(quizAttempt?.feedback as Feedback | undefined);

	function findDecision(itemId: string): Decision | undefined {
		return quizDecisions.find((d) => d.itemId === itemId);
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
	{#if !feedback}
		<section class="flex flex-col items-center justify-center gap-4">
			<p class="loading loading-spinner loading-xl"></p>
			<p class="text-center font-semibold">We are giving your feedback...</p>
		</section>
	{:else if feedback}
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

				{#if feedback.problem_topics.length > 0}
					<div class="mt-3">
						<p class="opacity-70">Problem topics:</p>
						<div class="flex flex-wrap gap-1">
							{#each feedback.problem_topics as topic}
								<span class="badge badge-soft badge-error">{topic}</span>
							{/each}
						</div>
					</div>
				{/if}

				{#if feedback.uncovered_topics.length > 0}
					<div class="mt-3">
						<p class="opacity-70">Uncovered topics:</p>
						<div class="flex flex-wrap gap-1">
							{#each feedback.uncovered_topics as topic}
								<span class="badge badge-soft badge-info">{topic}</span>
							{/each}
						</div>
					</div>
				{/if}
			</div>
		</section>
	{/if}

	<section class="flex flex-1 flex-col gap-3 sm:min-h-0">
		{#if quiz}
			<h1 class="text-center text-2xl font-bold leading-tight">{quiz?.title || 'Quiz'}</h1>
		{:else}
			<h1 class="text-center text-2xl font-bold leading-tight">Loading...</h1>
		{/if}

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
					{@const d = findDecision(item.id)}
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

		<div class="fixed bottom-12 left-0 right-0 z-10 p-4 sm:static sm:p-0">
			<Button block>Share Quiz</Button>
		</div>
	</section>
</div>
