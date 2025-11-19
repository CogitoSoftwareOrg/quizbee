<script lang="ts">
	import { X } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import posthog from 'posthog-js';

	import { Button } from '@quizbee/ui-svelte-daisy';

	import { pb } from '$lib/pb';
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
	import LegalCard from './LegalCard.svelte';
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
		posthog.reset();
		pb!.authStore.clear();
		goto('/sign-in');
	}
</script>

<div class="mx-auto w-full max-w-7xl space-y-4 p-4 sm:space-y-0 sm:p-6 lg:p-4">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<h1 class="mx-auto text-2xl font-bold sm:text-3xl">Profile & Settings</h1>
	</div>

	<!-- Main Grid Layout -->

	<!-- Left Column: Profile Info -->
	<div class="mx-auto max-w-xl space-y-0 sm:space-y-2 lg:col-span-1">
		<ProfileCard />

		<SubscriptionCard />

		<LegalCard />

		<!-- Logout Button -->
		<Button class="mt-4" onclick={logout} color="error" style="soft" block>
			<X class="h-4 w-4" />
			Logout
		</Button>
	</div>
</div>
