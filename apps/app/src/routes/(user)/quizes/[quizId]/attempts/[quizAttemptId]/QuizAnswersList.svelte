<script lang="ts">
	import posthog from 'posthog-js';
	import type { ClassValue } from 'svelte/elements';
	import { untrack } from 'svelte';

	import {
		pb,
		type QuizesResponse,
		type QuizItemsResponse,
		type QuizAttemptsResponse
	} from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Answer } from '$lib/apps/quizes/types';
	import { ChevronDown, ChevronRight, Info } from 'lucide-svelte';
	import { patchApi, putApi } from '$lib/api/call-api';
	import { QuizItemsStatusOptions } from '$lib/pb/pocketbase-types';

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

	const readyItems = $derived(
		quizItems.filter((item) => ['final', 'generated', 'generating'].includes(item.status))
	);
	const answeredItemIds = $derived(quizDecisions.map((decision) => decision.itemId));
	const readyItemsWithoutAnswers = $derived(
		readyItems.filter((item) => !answeredItemIds.includes(item.id))
	);

	function optionLabel(idx: number): string {
		return String.fromCharCode(65 + idx);
	}

	let expandedAnswers = $state<Record<number, boolean>>({});

	function setExpanded(index: number, expanded: boolean) {
		expandedAnswers = { ...expandedAnswers, [index]: expanded };
	}

	function toggleExpanded(index: number) {
		setExpanded(index, !isExpanded(index));
	}

	function isExpanded(index: number): boolean {
		return !!expandedAnswers[index];
	}

	// Track stable keys to avoid unnecessary recalculations
	let lastItemId = $state<string | null>(null);
	let lastDecisionKey = $state<string | null>(null);

	// Auto-expand answers when decision is made
	// Only react to item.id and itemDecision changes, not to object reference changes
	$effect(() => {
		const currentItemId = item?.id ?? null;

		// Reset when navigating to a new item (only by ID, not object reference)
		if (currentItemId !== lastItemId) {
			lastItemId = currentItemId;
			lastDecisionKey = null;
			expandedAnswers = {};
		}

		// Only process if there's a decision
		if (!itemDecision) return;

		// Create stable key from decision data
		const decisionKey = `${itemDecision.itemId}:${itemDecision.answerIndex}:${itemDecision.correct}`;

		// Skip if already processed this exact decision
		if (decisionKey === lastDecisionKey) return;
		lastDecisionKey = decisionKey;

		// Expand correct answer and user's choice
		// Use untrack to read answers without creating dependency
		untrack(() => {
			const nextExpanded: Record<number, boolean> = {};
			answers.forEach((answer, idx) => {
				nextExpanded[idx] = answer.correct || idx === itemDecision!.answerIndex;
			});
			expandedAnswers = nextExpanded;
		});
	});

	async function createFeedback() {
		if (!quizAttempt.id || quizAttempt.feedback) return;

		posthog.capture('quiz_feedback_started', {
			quizId: quiz.id,
			quizAttemptId: quizAttempt.id,
			itemId: item.id
		});
		const res = await putApi(`quiz_attempts/${quizAttempt.id}`, {});
		console.log(res);
	}
</script>

<div class={[className, 'min-w-0']}>
	{#if item.status === 'final' || item.status === 'generated'}
		<ul class={['mb-1 mt-1 flex flex-col gap-6 px-3 sm:px-12']}>
			{#each answers as answer, index}
				<li class="min-w-0">
					<article
						class={[
							'border-base-300 bg-base-200 focus-within:ring-primary/60 group w-full min-w-0 overflow-hidden rounded-2xl border text-left shadow-sm transition focus-within:outline-none focus-within:ring-2',
							!itemDecision ? 'hover:border-primary/50 hover:shadow-md' : '',
							itemDecision && answer.correct
								? 'border-success/40 bg-success/10 ring-success/60 ring-2'
								: '',
							itemDecision?.answerIndex === index && !answer.correct
								? 'border-error/40 bg-error/10 ring-error/60 ring-2'
								: ''
						]}
					>
						<button
							type="button"
							class="focus-visible:ring-primary/60 flex w-full min-w-0 cursor-pointer items-start gap-3 p-4 text-left transition focus-visible:outline-none focus-visible:ring-2"
							onclick={async () => {
								const toAnswer = readyItemsWithoutAnswers.length;
								if (!itemDecision) {
									itemDecision = {
										itemId: item!.id,
										answerIndex: index,
										correct: answer.correct
									};
									const newDecisions = [...quizDecisions, itemDecision];

									item.status = QuizItemsStatusOptions.final;

									await Promise.all([
										pb!.collection('quizAttempts').update(quizAttempt!.id, {
											choices: newDecisions
										}),
										pb!.collection('quizItems').update(item!.id, {
											status: 'final'
										})
									]);

									if (toAnswer === 3 && quizItems.some((qi) => ['blank'].includes(qi.status))) {
										const result = await patchApi(`quizes/${quiz?.id}`, {
											attempt_id: quizAttempt!.id,
											limit: 5,
											mode: 'continue'
										});
										console.log('Quiz settings updated:', result);
									}

									if (item.order + 1 === quizItems.length) {
										await createFeedback();
										return;
									}

									return;
								}

								if (!answers[index]?.explanation) return;
								toggleExpanded(index);
							}}
						>
							<span
								class={[
									'inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border font-semibold transition',
									itemDecision?.answerIndex === index
										? 'border-error text-error'
										: 'border-base-300 text-base-content/70',
									itemDecision && answer.correct ? 'border-success text-success' : ''
								]}>{optionLabel(index)}</span
							>
							{#if itemDecision}
								{#if isExpanded(index)}
									<ChevronDown size={28} />
								{:else}
									<ChevronRight size={28} />
								{/if}
							{/if}
							<div class="min-w-0 flex-1">
								<p class="wrap-break-words leading-relaxed">{@html answer.content}</p>
							</div>
							{#if itemDecision}
								<div class="ml-2 shrink-0">
									{#if answer.correct}
										<span class="badge badge-success">Correct</span>
									{:else if itemDecision?.answerIndex === index}
										<span class="badge badge-error">Your pick</span>
									{/if}
								</div>
							{/if}
						</button>

						{#if itemDecision && answers[index]?.explanation}
							<div
								class="grid transition-[grid-template-rows] duration-200 ease-out"
								style={`grid-template-rows: ${isExpanded(index) ? '1fr' : '0fr'}`}
							>
								<div class="min-h-0 overflow-hidden">
									<div
										class={[
											'border-t p-4',
											itemDecision?.answerIndex === index && !answer.correct
												? 'border-error/40 bg-error/10'
												: answer.correct
													? 'border-success/40 bg-success/10'
													: 'border-base-300/60 bg-base-200/80'
										]}
										aria-hidden={!isExpanded(index)}
									>
										<div class="flex items-start gap-3">
											<Info class="mt-0.5 shrink-0" size={18} />
											<div class="min-w-0 flex-1 space-y-1">
												<p class="text-xs font-semibold uppercase tracking-wide opacity-60">
													Explanation
												</p>
												<p class="wrap-break-words text-sm leading-relaxed opacity-80">
													{@html answer.explanation}
												</p>
											</div>
										</div>
									</div>
								</div>
							</div>
						{/if}
					</article>
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
