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
	import { userStore } from '$lib/apps/users/user.svelte.js';

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

	const user = $derived(userStore.user);

	const readyItems = $derived(
		quizItems.filter((item) => ['final', 'generated', 'generating'].includes(item.status))
	);
	const readyItemsWithoutAnswers = $derived(
		readyItems.filter((item) => !quizDecisions.at(item.order))
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
	let lastItemOrder = $state<number | null>(null);
	let lastDecisionKey = $state<string | null>(null);

	// Auto-expand answers when decision is made
	// Only react to item.order and itemDecision changes, not to object reference changes
	$effect(() => {
		const currentItemOrder = item?.order ?? null;

		// Reset when navigating to a new item (only by order, not object reference)
		if (currentItemOrder !== lastItemOrder) {
			lastItemOrder = currentItemOrder;
			lastDecisionKey = null;
			expandedAnswers = {};
		}

		// Only process if there's a decision
		if (!itemDecision) return;

		// Create stable key from decision data
		const decisionKey = `${itemDecision.answerIndex}:${itemDecision.correct}`;

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

	async function finalizeQuiz() {
		posthog.capture('quiz_finalize_started', {
			quizId: quiz.id,
			quizAttemptId: quizAttempt.id
		});
		const res = await putApi(`quizes/${quiz.id}/finalize`, {
			attempt_id: quizAttempt.id
		});
		console.log(res);
	}

	async function finalizeAttempt() {
		posthog.capture('attempt_finalize_started', {
			quizId: quiz.id,
			quizAttemptId: quizAttempt.id
		});
		const res = await putApi(`quizes/${quiz.id}/attempts/${quizAttempt.id}`, {});
		console.log(res);
	}
</script>

<div class={[className, 'min-w-0']}>
	{#if item.status === 'final' || item.status === 'generated'}
		<ul class={['mb-1 mt-1 flex flex-col gap-3 px-3 sm:px-12']}>
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
										answerIndex: index,
										correct: answer.correct
									};

									// Create new decisions array and place decision at the correct position (item.order)
									const newDecisions = [...quizDecisions];
									newDecisions[item.order] = itemDecision;

									item.status = QuizItemsStatusOptions.final;
									try {
										await pb!.collection('quizAttempts').update(quizAttempt!.id, {
											choices: newDecisions
										});
										await pb!.collection('quizItems').update(item!.id, {
											status: 'final'
										});
									} catch (error) {
										console.error(error);
										itemDecision = null;
										item.status = QuizItemsStatusOptions.generated;
									}

									if (toAnswer <= 2 && quizItems.some((qi) => ['blank'].includes(qi.status))) {
										const result = await patchApi(`quizes/${quiz?.id}`, {
											attempt_id: quizAttempt!.id,
											mode: 'continue'
										});
										console.log('Quiz settings updated:', result);
									}

									if (
										item.order + 1 === quizItems.length &&
										!(quizAttempt?.feedback as any)?.overview
									) {
										await finalizeAttempt();
									}

									if (item.order + 1 === quizItems.length && quiz.author === user?.id) {
										await finalizeQuiz();
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
												<p class="wrap-break-words leading-relaxed opacity-80 md:text-base">
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
		<div class="flex h-full flex-col items-center justify-center gap-8 px-4 py-16">
			<!-- Main Loading Container -->
			<div class="w-full max-w-md">
				<!-- Animated Header -->
				<div class="mb-8 text-center">
					<div class="mb-4 flex justify-center">
						<div class="relative h-24 w-24">
							<!-- Outer rotating ring -->
							<div
								class="border-t-primary border-r-primary absolute inset-0 animate-spin rounded-full border-4 border-transparent opacity-70"
							></div>
							<!-- Middle pulsing ring -->
							<div
								class="border-primary/30 absolute inset-2 animate-pulse rounded-full border-2"
							></div>
							<!-- Inner icon -->
							<div class="absolute inset-0 flex items-center justify-center">
								<div
									class="bg-primary/10 flex h-full w-full items-center justify-center rounded-full"
								>
									<span class="text-3xl">✨</span>
								</div>
							</div>
						</div>
					</div>
					<h2 class="text-base-content mb-2 text-2xl font-bold">Building Your Quiz</h2>
					<p class="text-base-content/70">We're preparing personalized questions just for you...</p>
				</div>

				<!-- Progress Indicators -->
				<div class="mb-8 hidden space-y-4 sm:block">
					<div class="flex items-center gap-3">
						<div
							class="bg-success/20 flex h-8 w-8 shrink-0 items-center justify-center rounded-full"
						>
							<span class="text-success">✓</span>
						</div>
						<div class="flex-1">
							<p class="text-base-content text-sm font-medium">Quiz initialized</p>
							<p class="text-base-content/60 text-xs">Ready to generate questions</p>
						</div>
					</div>

					<div class="flex items-center gap-3">
						<div
							class="bg-primary/20 flex h-8 w-8 shrink-0 animate-pulse items-center justify-center rounded-full"
						>
							<span class="text-primary">⚡</span>
						</div>
						<div class="flex-1">
							<p class="text-base-content text-sm font-medium">Generating questions</p>
							<p class="text-base-content/60 text-xs">Using AI to create unique challenges</p>
						</div>
					</div>

					<div class="flex items-center gap-3 opacity-50">
						<div
							class="border-base-300 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-dashed"
						>
							<span class="text-base-content/40">3</span>
						</div>
						<div class="flex-1">
							<p class="text-base-content text-sm font-medium">Ready to answer</p>
							<p class="text-base-content/60 text-xs">Questions will appear shortly</p>
						</div>
					</div>
				</div>

				<!-- Timeline Info -->
				<div class="bg-base-200/50 rounded-lg p-4 text-center">
					<p class="text-base-content/70 text-sm">
						<span class="text-base-content font-semibold">Usually takes less than 10 seconds</span>
						<br />
						<span class="text-xs">Your AI tutor is working hard! ⏱️</span>
					</p>
				</div>

				<!-- Animated dots -->
				<div class="mt-8 flex justify-center gap-2">
					<div
						class="bg-primary h-2 w-2 animate-bounce rounded-full"
						style="animation-delay: 0s"
					></div>
					<div
						class="bg-primary h-2 w-2 animate-bounce rounded-full"
						style="animation-delay: 0.2s"
					></div>
					<div
						class="bg-primary h-2 w-2 animate-bounce rounded-full"
						style="animation-delay: 0.4s"
					></div>
				</div>
			</div>
		</div>
	{/if}
</div>
