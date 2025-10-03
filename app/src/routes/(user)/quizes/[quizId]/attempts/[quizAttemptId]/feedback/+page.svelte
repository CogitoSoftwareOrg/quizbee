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

<div class="relative mx-auto flex h-full min-h-0 max-w-3xl flex-1 flex-col gap-6 p-1">
	{#if !feedback}
		<div class="flex flex-col items-center justify-center gap-4">
			<p class="loading loading-spinner loading-xl"></p>
			<p class="text-center font-semibold">We are giving your feedback...</p>
		</div>
	{:else if quiz && feedback}
		<div class="flex w-full flex-col gap-6 px-3">
			<Button
				color="neutral"
				style="ghost"
				href={`/home`}
				class="absolute left-0 top-0 flex underline"
			>
				<ChevronLeft /> Back to home
			</Button>

			<section>
				<h1 class="text-center text-2xl font-bold leading-tight">{quiz.title || 'Quiz'}</h1>
				<p class="mt-1 text-center text-sm opacity-70">
					Score: {correctCount} / {quizItems.length}
				</p>

				<div class="mt-4 space-y-2">
					<p class="opacity-80">
						{feedback.overview}
					</p>
					<p class="opacity-70">
						Pay attention to the highlighted topics — they will help you improve.
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
			</section>
		</div>
	{/if}

	<section class="flex min-h-0 flex-1 flex-col gap-3">
		<Input
			class="w-full"
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
			<ul class="flex flex-1 flex-col gap-2 overflow-y-auto pr-1">
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
	</section>

	<section class="pt-2">
		<Button block>Share Quiz</Button>
	</section>
</div>
