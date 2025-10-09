<script lang="ts">
	import { Flame, Plus, Sparkles, Target } from 'lucide-svelte';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import AttemptsHistory from '$lib/apps/quiz-attempts/AttemptsHistory.svelte';

	import Button from '$lib/ui/Button.svelte';

	const quizAttempts = $derived(quizAttemptsStore.quizAttempts);
	const quizes = $derived(quizesStore.quizes);
	const materials = $derived(materialsStore.materials);

	// Filter attempts: only with feedback and quiz status 'final'
	const validAttempts = $derived.by(() => {
		if (!quizAttempts?.length || !quizes?.length) return [];
		return quizAttempts.filter((attempt) => {
			if (!attempt?.feedback) return false;
			const quiz = quizes.find((q) => q.id === attempt.quiz);
			return quiz?.status === 'final';
		});
	});

	function ensureChoicesArray(value: unknown) {
		if (!value) return [];
		if (Array.isArray(value)) return value;
		if (typeof value === 'string') {
			try {
				const parsed = JSON.parse(value);
				return Array.isArray(parsed) ? parsed : [];
			} catch (error) {
				return [];
			}
		}
		return [];
	}

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

	const weeklyQuestionCount = $derived.by(() => {
		if (!validAttempts?.length) return 0;
		const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;
		return validAttempts.reduce((sum, attempt) => {
			if (!attempt?.created) return sum;
			const createdAt = new Date(attempt.created).getTime();
			if (Number.isNaN(createdAt) || createdAt < cutoff) return sum;
			const choices = ensureChoicesArray(attempt.choices);
			return sum + choices.length;
		}, 0);
	});

	const weeklyProgress = $derived.by(() => {
		if (!weeklyGoal) return 0;
		const percentage = Math.round((weeklyQuestionCount / weeklyGoal) * 100);
		return Math.max(0, Math.min(100, percentage));
	});

	const streak = $derived.by(() => {
		if (!validAttempts?.length) return 0;
		let streakCounter = 0;
		let previousDay: Date | null = null;

		for (const attempt of validAttempts) {
			if (!attempt?.created) continue;

			const createdDate = new Date(attempt.created);
			if (Number.isNaN(createdDate.getTime())) continue;

			const currentDay = new Date(
				createdDate.getFullYear(),
				createdDate.getMonth(),
				createdDate.getDate()
			);

			if (!previousDay) {
				streakCounter = 1;
				previousDay = currentDay;
				continue;
			}

			const diffInDays = Math.round(
				(previousDay.getTime() - currentDay.getTime()) / (24 * 60 * 60 * 1000)
			);

			if (diffInDays === 0) {
				continue;
			}

			if (diffInDays === 1) {
				streakCounter += 1;
				previousDay = currentDay;
				continue;
			}

			break;
		}

		return streakCounter;
	});

	const latestAttempt = $derived(validAttempts?.[0]);

	const latestAttemptSummary = $derived.by(() => {
		const attempt = latestAttempt;
		if (!attempt) return null;
		const quiz = quizes?.find((candidate) => candidate.id === attempt.quiz) ?? null;
		const choices = ensureChoicesArray(attempt.choices);
		const correctCount = choices.filter((choice) => Boolean(choice?.correct)).length;
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
	class="mx-auto flex min-h-full w-full max-w-7xl flex-col gap-4 py-4 sm:gap-6 sm:px-6 sm:py-6 lg:gap-8 lg:px-8 lg:py-8"
>
	<!-- CTA Section -->
	<section class="flex justify-center">
		<Button
			wide
			size="xl"
			style="solid"
			href="/quizes/new"
			class="ring-primary/20 hover:ring-primary/40 shadow-2xl ring-2 transition-all"
		>
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
				<p class="text-base-content/60 mt-1.5 text-xs sm:mt-2 sm:text-sm">
					Past 7 days across all attempts
				</p>
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
