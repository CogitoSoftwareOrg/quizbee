<script lang="ts">
	import { Flame, Plus, Sparkles, Target, Crown } from 'lucide-svelte';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte.js';
	import AttemptsHistory from '$lib/apps/quiz-attempts/AttemptsHistory.svelte';
	import Button from '$lib/ui/Button.svelte';
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
	class="mx-auto flex min-h-full w-full max-w-7xl flex-col gap-4 py-1 sm:gap-6 sm:px-6 sm:py-2 lg:gap-8 lg:px-8 lg:py-4"
>
	<!-- Upgrade Reminder for Free Plan -->
	{#if isFreePlan}
		<button
			onclick={() => {
				uiStore.setPaywallOpen(true);
			}}
			class="border-warning/30 hover:border-warning/50 group relative cursor-pointer overflow-hidden rounded-2xl border p-4 shadow-lg transition-all hover:shadow-xl sm:rounded-3xl sm:p-5 md:p-6"
		>
			<div class="relative z-10 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
				<div class="flex items-start gap-3 sm:items-center sm:gap-4">
					<div
						class="bg-warning/20 text-warning rounded-xl p-2.5 transition-transform group-hover:scale-110 sm:p-3"
					>
						<Crown size={24} class="sm:size-7" />
					</div>
					<div class="space-y-1">
						<h3 class="text-base-content text-base font-bold leading-tight sm:text-lg md:text-xl">
							Unlock unlimited possibilities
						</h3>
						<p class="text-base-content/70 text-xs leading-relaxed sm:text-sm md:text-base">
							Upgrade to Plus or Pro for unlimited quizzes, advanced AI features, and priority
							support
						</p>
					</div>
				</div>
				<div
					class="bg-warning text-warning-content group-hover:bg-warning/90 ml-auto inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold shadow-md transition-all group-hover:shadow-lg sm:ml-0 sm:px-5 sm:py-3 sm:text-base"
				>
					View Plans
					<Sparkles size={16} class="sm:size-5" />
				</div>
			</div>
			<div
				class="from-warning/5 pointer-events-none absolute inset-0 bg-gradient-to-r to-transparent opacity-0 transition-opacity group-hover:opacity-100"
			></div>
		</button>
	{/if}

	<!-- CTA Section -->
	<section class="flex justify-center">
		<Button wide size="xl" style="solid" href="/quizes/new" class="shadow-2xl transition-all">
			<Plus size={24} /> Start New Quiz
		</Button>
	</section>

	<!-- Hero Section -->
	<section
		class="from-primary/50 via-primary/40 to-secondary/50 text-base-content rounded-2xl bg-gradient-to-br p-4 shadow-lg sm:rounded-3xl sm:p-6 md:p-8 lg:p-10"
	>
		<div class="mb-4 max-w-3xl space-y-2 sm:mb-6 sm:space-y-3">
			<p class="text-base-content/60 text-xs font-medium uppercase tracking-widest">
				Personal Dashboard
			</p>
			<h1
				class="text-2xl font-bold leading-tight tracking-tight sm:text-3xl md:text-4xl lg:text-5xl"
			>
				Stay consistent and keep sharpening your recall
			</h1>
			<p class="text-base-content/70 text-sm leading-relaxed sm:text-base md:text-lg">
				Monitor streaks, review performance, and jump straight into a new quiz when you're ready.
			</p>
		</div>

		<!-- Stats Cards Grid -->
		<div class="grid gap-3 sm:gap-4 md:grid-cols-2 lg:grid-cols-3">
			<!-- Weekly Questions Card -->
			<article
				class="bg-base-100 border-base-300 group rounded-xl border p-4 shadow-lg transition-all hover:shadow-xl sm:rounded-2xl sm:p-5 md:p-6"
			>
				<div class="flex items-center justify-between">
					<span class="text-base-content/70 text-xs font-medium sm:text-sm"
						>Questions this week</span
					>
					<div class="bg-primary/10 text-primary rounded-lg p-1.5 sm:p-2">
						<Target size={18} class="sm:size-5" />
					</div>
				</div>
				<p class="text-base-content mt-3 text-3xl font-bold sm:mt-4 sm:text-4xl">
					{weeklyQuestionCount}
				</p>
				<p class="text-base-content/60 mt-1.5 text-xs sm:mt-2 sm:text-sm">This week (Mon-Sun)</p>
				<div class="mt-3 space-y-1.5 sm:mt-4 sm:space-y-2">
					<div class="bg-base-300 h-2 w-full overflow-hidden rounded-full sm:h-2.5">
						<div
							class="bg-primary h-full rounded-full transition-all duration-500"
							style={`width: ${weeklyProgress}%`}
						></div>
					</div>
					<p class="text-base-content/70 text-xs font-medium">
						{weeklyProgress}% of weekly goal ({weeklyGoal})
					</p>
				</div>
			</article>

			<!-- Streak Card -->
			<article
				class="bg-base-100 border-base-300 group rounded-xl border p-4 shadow-lg transition-all hover:shadow-xl sm:rounded-2xl sm:p-5 md:p-6"
			>
				<div class="flex items-center justify-between">
					<span class="text-base-content/70 text-xs font-medium sm:text-sm">Current streak</span>
					<div class="bg-warning/10 text-warning rounded-lg p-1.5 sm:p-2">
						<Flame size={18} class="sm:size-5" />
					</div>
				</div>
				<p class="text-base-content mt-3 text-3xl font-bold sm:mt-4 sm:text-4xl">
					{streak}
					<span class="text-xl font-normal sm:text-2xl">{streak === 1 ? 'day' : 'days'}</span>
				</p>
				<p class="text-base-content/60 mt-1.5 text-xs sm:mt-2 sm:text-sm">
					Keep it going! Practice daily to maintain your streak
				</p>
			</article>

			<!-- Latest Attempt Card -->
			<a
				href={latestAttempt
					? `/quizes/${latestAttempt.quiz}/attempts/${latestAttempt.id}/feedback`
					: '/quizes/new'}
				class="bg-base-100 border-base-300 group rounded-xl border p-4 shadow-lg transition-all hover:scale-[1.02] hover:shadow-xl sm:rounded-2xl sm:p-5 md:col-span-2 md:p-6 lg:col-span-1"
			>
				<div class="flex items-center justify-between">
					<span class="text-base-content/70 text-xs font-medium sm:text-sm">Latest attempt</span>
					<div
						class="bg-secondary/10 text-secondary rounded-lg p-1.5 transition-transform group-hover:rotate-12 sm:p-2"
					>
						<Sparkles size={18} class="sm:size-5" />
					</div>
				</div>
				{#if latestAttemptSummary}
					<p
						class="text-base-content mt-3 line-clamp-2 text-base font-semibold leading-snug sm:mt-4 sm:text-lg"
					>
						{latestAttemptSummary.title}
					</p>
					<p class="text-base-content/60 mt-1 text-xs sm:mt-1.5 sm:text-sm">
						Completed {formatDate(latestAttemptSummary.created)}
					</p>
					<div class="mt-3 flex flex-wrap items-center gap-1.5 text-xs sm:mt-4 sm:gap-2 sm:text-sm">
						<span class="badge badge-success gap-1 font-medium">
							{latestAttemptSummary.correctCount} correct
						</span>
						<span class="badge badge-info gap-1 font-medium">
							{latestAttemptSummary.totalCount} total
						</span>
					</div>
					{#if latestAttemptSummary.score !== null}
						<div
							class="bg-base-200 mt-3 inline-block rounded-lg px-2.5 py-1 sm:mt-4 sm:px-3 sm:py-1.5"
						>
							<p class="text-base-content text-base font-bold sm:text-lg">
								{latestAttemptSummary.score}%
								<span class="text-base-content/60 text-xs font-normal sm:text-sm">accuracy</span>
							</p>
						</div>
					{/if}
				{:else}
					<p class="text-base-content mt-3 text-base font-semibold sm:mt-4 sm:text-lg">
						No attempts yet
					</p>
					<p class="text-base-content/60 mt-1.5 text-xs sm:mt-2 sm:text-sm">
						Launch your first quiz to start building history
					</p>
					<div
						class="bg-base-200 group-hover:bg-base-300 mt-3 inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors sm:mt-4 sm:gap-2 sm:px-3 sm:py-2 sm:text-sm"
					>
						<Plus size={14} class="sm:size-4" />
						Start Now
					</div>
				{/if}
			</a>
		</div>
	</section>

	<!-- History Section -->
	<section
		class="border-base-300 bg-base-100 rounded-2xl border p-4 shadow-lg sm:rounded-3xl sm:p-5 md:p-6 lg:p-8"
	>
		<h2 class="text-base-content mb-4 text-xl font-bold sm:mb-5 sm:text-2xl">Quiz History</h2>
		<AttemptsHistory
			class="h-[400px] sm:h-[480px] md:h-[520px]"
			{quizAttempts}
			{quizes}
			{materials}
		/>
	</section>
</div>
