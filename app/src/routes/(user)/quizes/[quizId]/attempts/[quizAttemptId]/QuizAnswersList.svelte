<script lang="ts">
	import type { ClassValue } from 'svelte/elements';

	import {
		pb,
		type QuizesResponse,
		type QuizItemsResponse,
		type QuizAttemptsResponse
	} from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Answer } from '$lib/apps/quizes/types';
	import { computeApiUrl } from '$lib/api/compute-url';
	import { Info } from 'lucide-svelte';

	interface Props {
		class?: ClassValue;
		answers: Answer[];
		quizItems: QuizItemsResponse[];
		quizDecisions: Decision[];
		quiz: QuizesResponse;
		item: QuizItemsResponse;
		itemDecision: Decision | null;
		quizAttempt: QuizAttemptsResponse;
	}

	let {
		class: className,
		answers,
		quizItems,
		quizDecisions,
		quiz,
		item,
		quizAttempt,
		itemDecision = $bindable(null)
	}: Props = $props();

	const readyItemsWithoutDecisions = $derived(
		quizItems.filter((i) => !quizDecisions.some((d) => d.itemId === i.id) && i.status === 'final')
	);

	function optionLabel(idx: number): string {
		return String.fromCharCode(65 + idx);
	}
</script>

<div class={[className]}>
	{#if item.status === 'final'}
		<ul class={['flex flex-col gap-6 px-12']}>
			{#each answers as answer, index}
				<li class={['space-y-2']}>
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

							const newDecisions = [...quizDecisions, itemDecision];
							await pb!.collection('quizAttempts').update(quizAttempt!.id, {
								choices: newDecisions
							});
						}}
					>
						<div class="flex items-start gap-3 p-4">
							<span
								class={[
									'inline-flex h-8 w-8 items-center justify-center rounded-full border font-semibold',
									itemDecision?.answerIndex === index
										? 'border-error text-error'
										: 'border-base-300 text-base-content/70',
									itemDecision && answer.correct ? 'border-success text-success' : ''
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
					{#if itemDecision}
						{#if answers[index]?.explanation}
							<div
								class={[
									'rounded-xl border p-4 shadow-sm',
									index === itemDecision?.answerIndex && !answer.correct
										? 'border-error/50 bg-error/10'
										: answer.correct
											? 'border-success/50 bg-success/10'
											: 'border-base-300 bg-base-200'
								]}
							>
								<div class="mb-1 flex items-center gap-2">
									<Info class="mt-0.5" size={18} />
									<span class="text-xs font-semibold uppercase tracking-wide opacity-60"
										>Explanation</span
									>
								</div>
								<p class="text-sm opacity-80">{answer.explanation}</p>
							</div>
						{/if}
					{/if}
				</li>
			{/each}
		</ul>
	{:else}
		<div class="flex h-full flex-col items-center justify-center gap-4">
			<p class="loading loading-spinner loading-xl"></p>
			<p class="text-center font-semibold">We are building your quiz...</p>
		</div>
	{/if}
</div>
