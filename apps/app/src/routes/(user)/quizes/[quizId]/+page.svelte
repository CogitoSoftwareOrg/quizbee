<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { Clock, Search, BookOpen, Play, ChevronDown, ChevronRight } from 'lucide-svelte';

	import { Button, Input } from '@quizbee/ui-svelte-daisy';

	import { userStore } from '$lib/apps/users/user.svelte.js';
	import { pb } from '$lib/pb/client.js';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte.js';
	import ShareQuizButton from '$lib/apps/quizes/ShareQuizButton.svelte';
	import ToggleQuizVisibility from '$lib/apps/quizes/ToggleQuizVisibility.svelte';
	import type { QuizExpand, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import { QuizesVisibilityOptions } from '$lib/pb';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';

	const { data } = $props();
	const quiz = $derived(
		quizesStore.quizes.find((q) => q.id === page.params.quizId) || data.pageQuiz
	);

	const user = $derived(userStore.user);
	const subscription = $derived(subscriptionStore.subscription);

	const forceStart = $derived(page.url.searchParams.get('forceStart') === 'true');

	// Get quiz items for this quiz
	const quizItems = $derived(
		quizItemsStore.quizItemsMap.get(quiz?.id || '') ||
			(quiz?.expand as QuizExpand)?.quizItems_via_quiz ||
			[]
	);

	// Filter quiz attempts for this specific quiz
	const quizAttempts = $derived(
		quizAttemptsStore.quizAttempts.filter(
			(attempt) => attempt.quiz === quiz?.id && attempt.feedback
		)
	);

	// Check if there's at least one completed attempt
	const hasCompletedAttempt = $derived(quizAttempts.some((attempt) => Boolean(attempt.feedback)));

	// Search for quiz items
	let searchQuery = $state('');
	let filteredItems: QuizItemsResponse[] = $state([]);
	$effect(() => {
		const q = searchQuery.trim().toLowerCase();
		const items = (quizItems as unknown as QuizItemsResponse[]) || [];
		filteredItems = q
			? items.filter((item) => {
					const question = (item.question || '').toLowerCase();
					return question.includes(q);
				})
			: items;
	});

	let expandedItems = $state<Record<string, boolean>>({});

	function setItemExpanded(itemId: string, expanded: boolean) {
		expandedItems = { ...expandedItems, [itemId]: expanded };
	}

	function toggleItemExpanded(itemId: string) {
		setItemExpanded(itemId, !isItemExpanded(itemId));
	}

	function isItemExpanded(itemId: string): boolean {
		return !!expandedItems[itemId];
	}

	function formatDateTime(value: string): string {
		if (!value) return '';
		try {
			return new Intl.DateTimeFormat(undefined, {
				dateStyle: 'medium',
				timeStyle: 'short'
			}).format(new Date(value));
		} catch (error) {
			return value;
		}
	}

	function getAttemptScore(attempt: any): { correct: number; total: number } {
		const decisions = (attempt.choices as Decision[]) || [];
		return {
			correct: decisions.filter((d) => d.correct).length,
			total: decisions.length
		};
	}

	async function startQuiz(force = false) {
		if (!user || !quiz) return;
		sessionStorage.removeItem('postLoginPath');
		const attempt = await pb!.collection('quizAttempts').create({
			user: user.id,
			quiz: quiz.id
		});
		if (force) quizAttemptsStore.add(attempt);

		await goto(`/quizes/${quiz.id}/attempts/${attempt.id}`);
	}

	onMount(async () => {
		if (!forceStart || !user || !quiz) return;
		await startQuiz(true);
	});
</script>

<div
	class="relative mx-auto flex max-w-7xl flex-1 flex-col gap-6 p-1 pb-20 sm:h-full sm:flex-row sm:pb-1"
>
	<!-- Left column: Quiz info and questions -->
	<section class="flex flex-1 flex-col gap-4 sm:min-h-0">
		{#if quiz}
			<div class="bg-base-200 space-y-4 rounded-2xl p-4">

				
				<div class="flex flex-wrap items-start justify-between gap-3">
					<h1 class="text-3xl font-bold leading-tight">{quiz.title || 'Quiz'}</h1>

					<!-- {#if quiz?.summary}
					<p class="text-base-content/70 text-sm">{quiz.summary}</p>
					{/if} -->

					{#if quiz.visibility === QuizesVisibilityOptions.public || quiz.visibility === QuizesVisibilityOptions.search}
						<ShareQuizButton block quizId={quiz.id} quizTitle={quiz.title || 'Quiz'} />
					{/if}
				</div>

				

				{#if user?.id === quiz.author}
					<ToggleQuizVisibility
						quizId={quiz.id}
						visibility={quiz.visibility || QuizesVisibilityOptions.private}
					/>
				{/if}

				<!-- {#if user?.id === quiz.author && quiz.materials && quiz.materials.length > 0}
					<div>
						<p class="text-base-content/70 mb-2 text-sm font-medium">Materials:</p>
						<div class="flex flex-wrap gap-2">
							{#each quiz.materials as materialId}
								<span class="badge badge-outline">
									{materialId}
								</span>
							{/each}
						</div>
					</div>
				{/if}

				<div class="border-base-300 border-t pt-4">
					<p class="text-base-content/70 mb-2 text-sm">
						Total questions: <span class="font-semibold">{quizItems.length}</span>
					</p>
				</div> -->
			</div>

			<div class="bg-base-200 flex flex-1 flex-col gap-3 rounded-2xl p-4 sm:min-h-0">
				<div class="sm:shrink-0">
					<h2 class="text-2xl font-semibold">Attempts History</h2>
					<div class="py-2 sm:shrink-0">
						<Button block color="primary" onclick={() => startQuiz(false)}>
							<Play size={18} />
							Start New Attempt
						</Button>
					</div>
					<p class="text-base-content/70 mt-1 text-sm">
						{quizAttempts.length}
						{quizAttempts.length === 1 ? 'attempt' : 'attempts'}
					</p>
				</div>

				{#if quizAttempts.length === 0}
					<div
						class="border-base-200 bg-base-100 flex flex-col items-center gap-3 rounded-xl border p-8 text-center shadow-sm"
					>
						<BookOpen class="opacity-40" size={48} />
						<div>
							<p class="font-medium">No attempts yet</p>
							<p class="text-base-content/70 text-sm">
								Start your first quiz attempt to see it here.
							</p>
						</div>
					</div>
				{:else}
					<ul class="flex flex-1 flex-col gap-3 pr-1 sm:min-h-0 sm:overflow-y-auto">
						{#each quizAttempts as attempt}
							{@const score = getAttemptScore(attempt)}
							{@const hasCompleted = Boolean(attempt.feedback)}
							<li>
								<a
									class="border-base-200 hover:bg-base-200/60 bg-base-100 group flex flex-col gap-3 rounded-xl border p-4 no-underline shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
									href={hasCompleted
										? `/quizes/${quiz?.id}/attempts/${attempt.id}/feedback`
										: `/quizes/${quiz?.id}/attempts/${attempt.id}`}
								>
									<div class="flex items-start justify-between gap-3">
										<div class="flex-1">
											<div class="text-base-content/70 flex items-center gap-2 text-sm">
												<Clock size={14} class="opacity-60" />
												<span>{formatDateTime(attempt.updated)}</span>
											</div>
										</div>
										<div class="flex items-center gap-2">
											{#if hasCompleted}
												<span class="badge badge-primary badge-lg">
													{score.correct} / {score.total}
												</span>
											{:else}
												<span class="badge badge-outline badge-lg"> In Progress </span>
											{/if}
										</div>
									</div>

									{#if hasCompleted}
										<div class="text-base-content/70 text-sm">
											<p>✓ Completed</p>
										</div>
									{:else}
										<div class="text-base-content/70 text-sm">
											<p>Continue where you left off</p>
										</div>
									{/if}
								</a>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		{:else}
			<div class="flex flex-1 items-center justify-center">
				<p class="loading loading-spinner loading-lg"></p>
			</div>
		{/if}
	</section>

	<!-- Right column: Quiz attempts history -->
	<section class="bg-base-200 flex flex-1 flex-col gap-4 rounded-2xl p-4 sm:min-h-0">
		<h2 class="text-xl text-center font-semibold">Questions</h2>

		<Input
			class="w-full sm:shrink-0"
			placeholder="Search questions..."
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
			<p class="py-6 text-center opacity-70">
				{searchQuery ? 'Nothing found' : 'No questions yet'}
			</p>
		{:else}
			<ul class="flex flex-1 flex-col gap-2 pr-1 sm:min-h-0 sm:overflow-y-auto">
				{#each filteredItems as item, index}
					<li class="hover:bg-base-200 border-base-300 flex flex-col rounded-lg border transition">
						<button
							type="button"
							class="focus-visible:ring-primary/60 flex w-full items-start gap-3 p-3 text-left transition focus-visible:outline-none focus-visible:ring-2"
							onclick={() => toggleItemExpanded(item.id)}
						>
							<span class="text-base-content/50 min-w-6 text-sm font-medium">
								{index + 1}.
							</span>
							<p class="text-base-content/80 flex-1 text-sm leading-relaxed">
								{item.question}
							</p>
							<span class="ml-2 shrink-0">
								{#if isItemExpanded(item.id)}
									<ChevronDown size={20} />
								{:else}
									<ChevronRight size={20} />
								{/if}
							</span>
						</button>

						{#if item.answers && Array.isArray(item.answers)}
							<div
								class="grid transition-[grid-template-rows] duration-200 ease-out"
								style={`grid-template-rows: ${isItemExpanded(item.id) ? '1fr' : '0fr'}`}
							>
								<div class="min-h-0 overflow-hidden">
									<div class="border-base-200 border-t px-3 pb-3 pt-2">
										<ul class="space-y-2">
											{#each item.answers as answer, answerIndex}
												{@const shouldHighlight = hasCompletedAttempt && answer.correct}
												<li
													class="pl-6 text-sm leading-relaxed {shouldHighlight
														? 'text-success font-medium'
														: 'text-base-content/70'}"
												>
													<span class="mr-2 font-medium"
														>{String.fromCharCode(65 + answerIndex)}.</span
													>
													{answer.content}
													{#if shouldHighlight}
														<span class="text-success ml-2">✓</span>
													{/if}
												</li>
											{/each}
										</ul>
									</div>
								</div>
							</div>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	</section>
</div>
