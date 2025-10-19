<script lang="ts">
	import { BarChart, TrendingUp } from 'lucide-svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import {
		getValidAttempts,
		calculateWeeklyQuestionCount,
		calculateWeeklyProgress,
		calculateStreak,
		calculateAverageScore,
		calculateTotalQuizzes
	} from '$lib/apps/analytics/analytics-utils';

	// Import analytics widgets
	import StreakCard from './StreakCard.svelte';
	import WeeklyQuestionsCard from './WeeklyQuestionsCard.svelte';
	import TotalQuizzesCard from './TotalQuizzesCard.svelte';
	import AverageScoreCard from './AverageScoreCard.svelte';

	// Get data from stores
	const quizAttempts = $derived(quizAttemptsStore.quizAttempts);
	const quizes = $derived(quizesStore.quizes);

	// Calculate analytics
	const validAttempts = $derived(getValidAttempts(quizAttempts, quizes));
	const streak = $derived(calculateStreak(validAttempts));
	const weeklyQuestionCount = $derived(calculateWeeklyQuestionCount(validAttempts));
	const averageScore = $derived(calculateAverageScore(validAttempts));
	const totalQuizzes = $derived(calculateTotalQuizzes(validAttempts));

	const weeklyGoal = 200;
	const weeklyProgress = $derived(calculateWeeklyProgress(weeklyQuestionCount, weeklyGoal));
</script>

<div class="mx-auto w-full max-w-7xl space-y-4 p-4 sm:space-y-6 sm:p-6 lg:p-8">
	<!-- Header -->
	<div class="flex items-center gap-3">
		<BarChart class="h-8 w-8" />
		<div>
			<h1 class="text-2xl font-bold sm:text-3xl">Analytics</h1>
			<p class="text-sm opacity-70">Track your learning progress and performance</p>
		</div>
	</div>

	<!-- Statistics Overview -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold">Overview</h2>
		<div class="grid grid-cols-1 gap-3 sm:gap-4 md:grid-cols-2 lg:grid-cols-4">
			<StreakCard {streak} />
			<WeeklyQuestionsCard {weeklyQuestionCount} />
			<TotalQuizzesCard {totalQuizzes} />
			<AverageScoreCard {averageScore} />
		</div>
	</section>

	<!-- Weekly Progress Card -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold">Weekly Progress</h2>
		<div class="card bg-base-100 shadow-lg">
			<div class="card-body">
				<div class="flex items-center gap-2">
					<TrendingUp class="h-5 w-5" />
					<h3 class="card-title text-lg">This Week's Goal</h3>
				</div>
				<div class="mt-4 space-y-3">
					<div class="flex items-baseline justify-between">
						<div>
							<span class="text-3xl font-bold">{weeklyQuestionCount}</span>
							<span class="text-xl opacity-70"> / {weeklyGoal}</span>
							<span class="ml-2 text-sm opacity-60">questions</span>
						</div>
						<div class="text-right">
							<div class="text-2xl font-bold">{weeklyProgress}%</div>
							<div class="text-xs opacity-60">completed</div>
						</div>
					</div>
					<progress class="progress progress-primary w-full" value={weeklyProgress} max="100"
					></progress>
					<p class="text-sm opacity-70">
						{#if weeklyProgress >= 100}
							🎉 Congratulations! You've achieved your weekly goal!
						{:else}
							{weeklyGoal - weeklyQuestionCount} more questions to reach your goal
						{/if}
					</p>
				</div>
			</div>
		</div>
	</section>

	<!-- Performance Insights -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold">Performance Insights</h2>
		<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
			<!-- Accuracy Card -->
			<div class="card bg-base-100 shadow-lg">
				<div class="card-body">
					<h3 class="card-title text-lg">Average Accuracy</h3>
					<div class="mt-4">
						<div class="text-5xl font-bold">{averageScore}%</div>
						<p class="mt-2 text-sm opacity-70">Based on your last 10 quiz attempts</p>
					</div>
					<div class="mt-4">
						<div class="flex justify-between text-xs opacity-70">
							<span>Target: 80%</span>
							<span
								class={averageScore >= 80
									? 'text-success font-semibold'
									: 'text-warning font-semibold'}
							>
								{averageScore >= 80 ? '✓ On track' : '⚠ Needs improvement'}
							</span>
						</div>
					</div>
				</div>
			</div>

			<!-- Consistency Card -->
			<div class="card bg-base-100 shadow-lg">
				<div class="card-body">
					<h3 class="card-title text-lg">Consistency</h3>
					<div class="mt-4">
						<div class="text-5xl font-bold">{streak}</div>
						<p class="mt-2 text-sm opacity-70">
							{streak === 1 ? 'day streak' : 'days streak'}
						</p>
					</div>
					<div class="mt-4">
						<p class="text-sm opacity-70">
							{#if streak >= 7}
								🔥 Amazing! You're on fire with a week+ streak!
							{:else if streak >= 3}
								💪 Great job! Keep the momentum going!
							{:else if streak > 0}
								👍 Good start! Try to maintain daily practice.
							{:else}
								💡 Start a new streak by practicing today!
							{/if}
						</p>
					</div>
				</div>
			</div>
		</div>
	</section>

	<!-- Activity Summary -->
	<section class="space-y-4">
		<h2 class="text-lg font-semibold">Activity Summary</h2>
		<div class="card bg-base-100 shadow-lg">
			<div class="card-body">
				<div class="stats stats-vertical lg:stats-horizontal shadow">
					<div class="stat">
						<div class="stat-title">Total Quizzes</div>
						<div class="stat-value">{totalQuizzes}</div>
						<div class="stat-desc">All time completed</div>
					</div>

					<div class="stat">
						<div class="stat-title">This Week</div>
						<div class="stat-value text-primary">{weeklyQuestionCount}</div>
						<div class="stat-desc">Questions answered</div>
					</div>

					<div class="stat">
						<div class="stat-title">Avg Score</div>
						<div class="stat-value text-secondary">{averageScore}%</div>
						<div class="stat-desc">Last 10 attempts</div>
					</div>
				</div>
			</div>
		</div>
	</section>
</div>
