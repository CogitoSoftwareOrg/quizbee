<script lang="ts">
	import { Flame, Plus, Sparkles, Target, Crown } from 'lucide-svelte';

	import { Button } from '@quizbee/ui-svelte-daisy';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte.js';
	import AttemptsHistory from '$lib/apps/quiz-attempts/AttemptsHistory.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import {
		getValidAttempts,
		calculateWeeklyQuestionCount,
		calculateWeeklyProgress,
		calculateStreak,
		ensureChoicesArray
	} from '$lib/apps/analytics/analytics-utils';

	const quizAttempts = $derived(quizAttemptsStore.quizAttempts);
	const quizes = $derived(quizesStore.quizes);
	const materials = $derived(materialsStore.materials);
	const subscription = $derived(subscriptionStore.subscription);

	const isFreePlan = $derived(subscription?.tariff === 'free');

	// Filter valid attempts
	const validAttempts = $derived(getValidAttempts(quizAttempts, quizes));

	function formatDate(value: string) {
		if (!value) return '';
		try {
			return new Intl.DateTimeFormat(undefined, {
				dateStyle: 'medium'
			}).format(new Date(value));
		} catch (error) {
			return value;
		}
	}

	const weeklyGoal = 200;
	const weeklyQuestionCount = $derived(calculateWeeklyQuestionCount(validAttempts));
	const weeklyProgress = $derived(calculateWeeklyProgress(weeklyQuestionCount, weeklyGoal));
	const streak = $derived(calculateStreak(validAttempts));

	const latestAttempt = $derived(validAttempts?.[0]);

	const latestAttemptSummary = $derived.by(() => {
		const attempt = latestAttempt;
		if (!attempt) return null;
		const quiz = quizes?.find((candidate) => candidate.id === attempt.quiz) ?? null;
		const choices = ensureChoicesArray(attempt.choices);
		const correctCount = choices.filter((choice) =>
			Boolean((choice as { correct: boolean }).correct)
		).length;
		const totalCount = choices.length;
		const score = totalCount === 0 ? null : Math.round((correctCount / totalCount) * 100);

		return {
			title: quiz?.title ?? 'Untitled quiz',
			created: attempt.created,
			correctCount,
			totalCount,
			score
		};
	});
</script>

<div
	class="mx-auto flex min-h-full w-full max-w-7xl flex-col gap-4 py-1 sm:gap-6 sm:px-6 lg:gap-8 lg:px-8"
>
	<!-- Upgrade Reminder for Free Plan -->
	{#if isFreePlan}
		<button
			onclick={() => {
				uiStore.setPaywallOpen(true);
			}}
			class="group relative cursor-pointer overflow-hidden rounded-2xl border border-warning/30 p-4 shadow-lg transition-all hover:border-warning/50 hover:shadow-xl sm:rounded-3xl sm:p-5 md:p-6"
		>
			<div class="relative z-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
				<div class="flex items-start gap-3 sm:items-center sm:gap-4">
					<div
						class="hidden rounded-xl bg-warning/20 p-2.5 text-warning transition-transform group-hover:scale-110 sm:block sm:p-3"
					>
						<Crown size={24} class="sm:size-7" />
					</div>
					<div class="space-y-1">
						<h3 class="text-base leading-tight font-bold text-base-content sm:text-lg md:text-xl">
							Unlock unlimited possibilities
						</h3>
						<p class="text-xs leading-relaxed text-base-content/70 sm:text-sm md:text-base">
							Upgrade to Plus or Pro for unlimited quizzes, advanced AI features, and priority
							support
						</p>
					</div>
				</div>
				<div
					class="mx-auto inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-warning-content shadow-md transition-all group-hover:bg-warning/90 group-hover:shadow-lg sm:mx-0 sm:mt-0 sm:ml-0 sm:px-5 sm:py-3 sm:text-base"
				>
					View Plans
					<Sparkles size={16} class="sm:size-5" />
				</div>
			</div>
			<div
				class="pointer-events-none absolute inset-0 bg-gradient-to-r from-warning/5 to-transparent opacity-0 transition-opacity group-hover:opacity-100"
			></div>
		</button>
	{/if}

	<!-- CTA Section -->
	{#if validAttempts.length > 0}
		<section class="hidden justify-center sm:flex">
			<Button
				color="primary"
				block
				size="xl"
				style="solid"
				href="/quizes/new"
				class="py-4 shadow-2xl sm:w-1/2"
			>
				<Plus size={24} /> Start New Quiz
			</Button>
		</section>
	{/if}

	{#if validAttempts.length === 0}
		<!-- Empty State CTA -->
		<section
			class="rounded-2xl bg-warning/20 from-primary/50 via-primary/40 to-secondary/50 p-8 text-base-content shadow-lg sm:rounded-3xl sm:p-12 md:p-16 lg:p-20"
		>
			<div class="mx-auto max-w-3xl space-y-6 text-center sm:space-y-8">
				<div
					class="mx-auto inline-flex items-center justify-center rounded-2xl bg-primary/10 p-4 sm:p-5"
				>
					<Sparkles size={32} class="text-primary sm:size-12" />
				</div>
				<div class="space-y-3 sm:space-y-4">
					<h1
						class="text-3xl leading-tight font-bold tracking-tight sm:text-4xl md:text-5xl lg:text-6xl"
					>
						Ready to Start Your Learning Journey?
					</h1>
					<p class="text-base leading-relaxed text-base-content/70 sm:text-lg md:text-xl">
						Create your first AI-powered quiz and begin tracking your progress. Transform your study
						materials into interactive quizzes in seconds.
					</p>
				</div>
				<div class="pt-4 sm:pt-6">
					<Button
						color="primary"
						size="xl"
						style="solid"
						href="/quizes/new"
						class="mx-auto inline-flex items-center gap-3 px-8 py-4 text-lg font-semibold shadow-2xl transition-all hover:scale-105 sm:px-10 sm:py-5 sm:text-xl"
					>
						<Plus size={24} class="sm:size-6" />
						Start New Quiz
					</Button>
				</div>
			</div>
		</section>
	{:else}
		<!-- Hero Section -->
		<section
			class="rounded-2xl bg-warning/20 from-primary/50 via-primary/40 to-secondary/50 p-4 text-base-content shadow-lg sm:rounded-3xl sm:p-6 md:p-8 lg:p-10"
		>
			<div class="mb-4 max-w-3xl space-y-2 sm:mb-6 sm:space-y-3">
				<p class="text-xs font-medium tracking-widest text-base-content/60 uppercase">
					Personal Dashboard
				</p>
				<h1
					class="text-2xl leading-tight font-bold tracking-tight sm:text-3xl md:text-4xl lg:text-5xl"
				>
					Stay consistent and keep sharpening your recall
				</h1>
				<p class="text-sm leading-relaxed text-base-content/70 sm:text-base md:text-lg">
					Monitor streaks, review performance, and jump straight into a new quiz when you're ready.
				</p>
			</div>

			<!-- Stats Cards Grid -->
			<div class="grid gap-3 sm:gap-4 md:grid-cols-2 lg:grid-cols-3">
				<!-- Weekly Questions Card -->
				<article
					class="group rounded-xl border border-base-300 bg-base-100 p-4 shadow-lg transition-all hover:shadow-xl sm:rounded-2xl sm:p-5 md:p-6"
				>
					<div class="flex items-center justify-between">
						<span class="text-xs font-medium text-base-content/70 sm:text-sm"
							>Questions this week</span
						>
						<div class="rounded-lg bg-primary/10 p-1.5 text-primary sm:p-2">
							<Target size={18} class="sm:size-5" />
						</div>
					</div>
					<p class="mt-3 text-3xl font-bold text-base-content sm:mt-4 sm:text-4xl">
						{weeklyQuestionCount}
					</p>
					<p class="mt-1.5 text-xs text-base-content/60 sm:mt-2 sm:text-sm">This week (Mon-Sun)</p>
					<div class="mt-3 space-y-1.5 sm:mt-4 sm:space-y-2">
						<div class="h-2 w-full overflow-hidden rounded-full bg-base-300 sm:h-2.5">
							<div
								class="h-full rounded-full bg-primary transition-all duration-500"
								style={`width: ${weeklyProgress}%`}
							></div>
						</div>
						<p class="text-xs font-medium text-base-content/70">
							{weeklyProgress}% of weekly goal ({weeklyGoal})
						</p>
					</div>
				</article>

				<!-- Streak Card -->
				<article
					class="group rounded-xl border border-base-300 bg-base-100 p-4 shadow-lg transition-all hover:shadow-xl sm:rounded-2xl sm:p-5 md:p-6"
				>
					<div class="flex items-center justify-between">
						<span class="text-xs font-medium text-base-content/70 sm:text-sm">Current streak</span>
						<div class="rounded-lg bg-warning/10 p-1.5 text-warning sm:p-2">
							<Flame size={18} class="sm:size-5" />
						</div>
					</div>
					<p class="mt-3 text-3xl font-bold text-base-content sm:mt-4 sm:text-4xl">
						{streak}
						<span class="text-xl font-normal sm:text-2xl">{streak === 1 ? 'day' : 'days'}</span>
					</p>
					<p class="mt-1.5 text-xs text-base-content/60 sm:mt-2 sm:text-sm">
						Keep it going! Practice daily to maintain your streak
					</p>
				</article>

				<!-- Latest Attempt Card -->
				<a
					href={latestAttempt
						? `/quizes/${latestAttempt.quiz}/attempts/${latestAttempt.id}/feedback`
						: '/quizes/new'}
					class="group rounded-xl border border-base-300 bg-base-100 p-4 shadow-lg transition-all hover:scale-[1.02] hover:shadow-xl sm:rounded-2xl sm:p-5 md:col-span-2 md:p-6 lg:col-span-1"
				>
					<div class="flex items-center justify-between">
						<span class="text-xs font-medium text-base-content/70 sm:text-sm">Latest attempt</span>
						<div
							class="rounded-lg bg-secondary/10 p-1.5 text-secondary transition-transform group-hover:rotate-12 sm:p-2"
						>
							<Sparkles size={18} class="sm:size-5" />
						</div>
					</div>
					{#if latestAttemptSummary}
						<p
							class="mt-3 line-clamp-2 text-base leading-snug font-semibold text-base-content sm:mt-4 sm:text-lg"
						>
							{latestAttemptSummary.title}
						</p>
						<p class="mt-1 text-xs text-base-content/60 sm:mt-1.5 sm:text-sm">
							Completed {formatDate(latestAttemptSummary.created)}
						</p>
						<div
							class="mt-3 flex flex-wrap items-center gap-1.5 text-xs sm:mt-4 sm:gap-2 sm:text-sm"
						>
							<span class="badge gap-1 font-medium badge-success">
								{latestAttemptSummary.correctCount} correct
							</span>
							<span class="badge gap-1 font-medium badge-info">
								{latestAttemptSummary.totalCount} total
							</span>
						</div>
						{#if latestAttemptSummary.score !== null}
							<div
								class="mt-3 inline-block rounded-lg bg-base-200 px-2.5 py-1 sm:mt-4 sm:px-3 sm:py-1.5"
							>
								<p class="text-base font-bold text-base-content sm:text-lg">
									{latestAttemptSummary.score}%
									<span class="text-xs font-normal text-base-content/60 sm:text-sm">accuracy</span>
								</p>
							</div>
						{/if}
					{:else}
						<p class="mt-3 text-base font-semibold text-base-content sm:mt-4 sm:text-lg">
							No attempts yet
						</p>
						<p class="mt-1.5 text-xs text-base-content/60 sm:mt-2 sm:text-sm">
							Launch your first quiz to start building history
						</p>
						<div
							class="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-base-200 px-2.5 py-1.5 text-xs font-medium transition-colors group-hover:bg-base-300 sm:mt-4 sm:gap-2 sm:px-3 sm:py-2 sm:text-sm"
						>
							<Plus size={14} class="sm:size-4" />
							Start Now
						</div>
					{/if}
				</a>
			</div>
		</section>
	{/if}
</div>
