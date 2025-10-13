<script lang="ts">
	import { X } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import { pb } from '$lib/pb';
	import Button from '$lib/ui/Button.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import {
		getValidAttempts,
		calculateWeeklyQuestionCount,
		calculateWeeklyProgress,
		calculateStreak,
		calculateAverageScore,
		calculateTotalQuizzes
	} from '$lib/apps/analytics/analytics-utils';

	// Import profile components
	import ProfileCard from './ProfileCard.svelte';
	import SubscriptionCard from './SubscriptionCard.svelte';
	import LearningGoalsCard from './LearningGoalsCard.svelte';
	import LearningTopicsCard from './LearningTopicsCard.svelte';

	// Import analytics widgets
	import StreakCard from '../analytics/StreakCard.svelte';
	import WeeklyQuestionsCard from '../analytics/WeeklyQuestionsCard.svelte';
	import TotalQuizzesCard from '../analytics/TotalQuizzesCard.svelte';
	import AverageScoreCard from '../analytics/AverageScoreCard.svelte';

	// Get data from stores
	const quizAttempts = $derived(quizAttemptsStore.quizAttempts);
	const quizes = $derived(quizesStore.quizes);
	const materials = $derived(materialsStore.materials);

	// Calculate analytics
	const validAttempts = $derived(getValidAttempts(quizAttempts, quizes));
	const streak = $derived(calculateStreak(validAttempts));
	const weeklyQuestionCount = $derived(calculateWeeklyQuestionCount(validAttempts));
	const averageScore = $derived(calculateAverageScore(validAttempts));
	const totalQuizzes = $derived(calculateTotalQuizzes(validAttempts));

	let weeklyGoal = $state(200);
	const weeklyProgress = $derived(calculateWeeklyProgress(weeklyQuestionCount, weeklyGoal));

	// Extract topics from materials
	const topics = $derived.by(() => {
		if (!materials?.length) return [];
		const topicSet = new Set<string>();

		materials.forEach((material) => {
			const title = material.title?.toLowerCase() || '';
			if (title.includes('med') || title.includes('bio') || title.includes('anatomy'))
				topicSet.add('Medical');
			if (title.includes('law') || title.includes('legal') || title.includes('court'))
				topicSet.add('Law');
			if (title.includes('eng') || title.includes('math') || title.includes('phys'))
				topicSet.add('Engineering');
			if (title.includes('bus') || title.includes('econ') || title.includes('finance'))
				topicSet.add('Business');
			if (title.includes('lang') || title.includes('language')) topicSet.add('Languages');
		});

		if (topicSet.size === 0) {
			return ['General Knowledge', 'Study Materials'];
		}

		return Array.from(topicSet);
	});

	function logout() {
		pb!.authStore.clear();
		goto('/sign-in');
	}
</script>

<div class="mx-auto w-full max-w-7xl space-y-4 p-4 sm:space-y-6 sm:p-6 lg:p-8">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold sm:text-3xl">Profile & Settings</h1>
	</div>

	<!-- Main Grid Layout -->
	<div class="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-3">
		<!-- Left Column: Profile Info -->
		<div class="space-y-4 sm:space-y-6 lg:col-span-1">
			<ProfileCard />

			<div class="divider"></div>

			<SubscriptionCard />

			<!-- Logout Button -->
			<Button onclick={logout} color="error" style="soft" block>
				<X class="h-4 w-4" />
				Logout
			</Button>
		</div>

		<!-- Right Column: Stats & Settings -->
		<div class="hidden space-y-4 sm:block sm:space-y-6 lg:col-span-2">
			<!-- Statistics Cards Grid -->
			<div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
				<StreakCard {streak} />
				<WeeklyQuestionsCard {weeklyQuestionCount} />
				<TotalQuizzesCard {totalQuizzes} />
				<AverageScoreCard {averageScore} />
			</div>

			<!-- Learning Goals -->
			<LearningGoalsCard {weeklyQuestionCount} {weeklyProgress} />

			<!-- Learning Topics -->
			<!-- <LearningTopicsCard {topics} /> -->
		</div>
	</div>
</div>
