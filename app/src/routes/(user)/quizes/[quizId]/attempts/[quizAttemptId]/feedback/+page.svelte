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

	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId) || null
	);
	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);

	const correctCount = $derived(quizDecisions.filter((d) => d.correct).length);

	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz));
	const quizItems = $derived(
		quiz?.expand.quizItems_via_quiz?.toSorted((a, b) => a.order - b.order) || []
	);

	function findDecision(itemId: string): Decision | undefined {
		return quizDecisions.find((d) => d.itemId === itemId);
	}

	function ensureAnswersArray(answers: unknown): Answer[] {
		if (!answers) return [];
		if (typeof answers === 'string') {
			try {
				const parsed = JSON.parse(answers);
				return Array.isArray(parsed) ? (parsed as Answer[]) : [];
			} catch (e) {
				return [];
			}
		}
		return (answers as Answer[]) || [];
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
					const answers = ensureAnswersArray(item.answers);
					return answers.some((a) => (a.content || '').toLowerCase().includes(q));
				})
			: items;
	});
</script>

<div class="mx-auto flex h-full min-h-0 max-w-3xl flex-1 flex-col gap-6 p-1">
	{#if !quizAttempt?.feedback}
		<div class="flex flex-col items-center justify-center gap-4">
			<p class="loading loading-spinner loading-xl"></p>
			<p class="text-center font-semibold">We are giving your feedback...</p>
		</div>
	{:else if quiz}
		<div class="flex w-full flex-col gap-6 px-3">
			<Button color="neutral" style="ghost" href={`/home`} class=" absolute left-0 top-0 flex">
				<ChevronLeft /> Back to home
			</Button>

			<section class="text-center">
				<h1 class="text-2xl font-bold leading-tight">{quiz.title || 'Quiz'}</h1>
				<p class="mt-1 text-sm opacity-70">Score: {correctCount} / {quizItems.length}</p>

				<div class="mt-4 space-y-2">
					<p class="opacity-80">
						Your results are ready. Below is the list of questions marked as correct or incorrect.
					</p>
					<p class="opacity-70">
						Pay attention to the highlighted topics — they will help you improve.
					</p>
				</div>

				<div class="mt-3 flex flex-wrap justify-center gap-2">
					<span class="badge">algorithms</span>
					<span class="badge">data structures</span>
					<span class="badge">syntax</span>
					<span class="badge">optimization</span>
					<span class="badge">terminology</span>
				</div>
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
									<span class={['badge', d.correct ? 'badge-success' : 'badge-neutral']}>
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
