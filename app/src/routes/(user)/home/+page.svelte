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

	const weeklyGoal = 70;

	const weeklyQuestionCount = $derived.by(() => {
		if (!quizAttempts?.length) return 0;
		const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;
		return quizAttempts.reduce((sum, attempt) => {
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
		if (!quizAttempts?.length) return 0;
		let streakCounter = 0;
		let previousDay: Date | null = null;

		for (const attempt of quizAttempts) {
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

	const latestAttempt = $derived(quizAttempts?.[0]);

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

<div class="mx-auto flex min-h-full w-full max-w-6xl flex-col gap-10 py-10 sm:px-6">
	<section class="flex justify-center">
		<Button wide size="xl" style="solid" href="/quizes/new" class="self-start md:self-center">
			<Plus size={24} /> Start New Quiz
		</Button>
	</section>

	<section
		class="from-primary/70 via-primary/50 to-secondary/70 text-primary-content rounded-3xl bg-gradient-to-r p-8 shadow-xl"
	>
		<div class="flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
			<div class="max-w-2xl space-y-4">
				<p class="text-primary-content/70 text-sm uppercase tracking-[0.3em]">Personal dashboard</p>
				<h1 class="text-4xl font-semibold tracking-tight">
					Stay consistent and keep sharpening your recall
				</h1>
				<p class="text-primary-content/80 text-base">
					Monitor streaks, review performance, and jump straight into a new quiz when you're ready.
				</p>
			</div>
		</div>

		<div class="mt-8 grid gap-4 sm:grid-cols-3">
			<article class="bg-primary-content/10 rounded-2xl p-5">
				<div class="flex items-center justify-between text-sm">
					<span class="text-primary-content/70">Questions this week</span>
					<Target size={18} class="opacity-80" />
				</div>
				<p class="mt-3 text-3xl font-semibold">{weeklyQuestionCount}</p>
				<p class="text-primary-content/70 mt-2 text-xs">Past 7 days across all attempts.</p>
				<div class="mt-4 space-y-2">
					<div class="bg-primary-content/20 h-2 w-full overflow-hidden rounded-full">
						<div
							class="bg-primary-content h-full rounded-full"
							style={`width: ${weeklyProgress}%`}
						></div>
					</div>
					<p class="text-primary-content/70 text-xs">
						{weeklyProgress}% of weekly goal ({weeklyGoal})
					</p>
				</div>
			</article>
			<article class="bg-primary-content/10 rounded-2xl p-5">
				<div class="flex items-center justify-between text-sm">
					<span class="text-primary-content/70">Current streak</span>
					<Flame size={18} class="opacity-80" />
				</div>
				<p class="mt-3 text-3xl font-semibold">{streak} {streak === 1 ? 'day' : 'days'}</p>
				<p class="text-primary-content/70 mt-2 text-xs">
					Count resets when a day slips without practice.
				</p>
			</article>
			<article class="bg-primary-content/10 rounded-2xl p-5">
				<div class="flex items-center justify-between text-sm">
					<span class="text-primary-content/70">Latest attempt</span>
					<Sparkles size={18} class="opacity-80" />
				</div>
				{#if latestAttemptSummary}
					<p class="mt-3 text-lg font-semibold leading-tight">{latestAttemptSummary.title}</p>
					<p class="text-primary-content/70 mt-1 text-xs">
						Completed {formatDate(latestAttemptSummary.created)}
					</p>
					<div class="mt-4 flex items-center gap-2 text-sm">
						<span class="badge badge-success">{latestAttemptSummary.correctCount} correct</span>
						<span class="badge badge-info">{latestAttemptSummary.totalCount} total</span>
					</div>
					{#if latestAttemptSummary.score !== null}
						<p class="text-primary-content/80 mt-3 text-lg font-semibold">
							{latestAttemptSummary.score}% accuracy
						</p>
					{/if}
				{:else}
					<p class="mt-3 text-lg font-semibold">No attempts yet</p>
					<p class="text-primary-content/70 mt-2 text-xs">
						Launch a quiz to start building your history.
					</p>
				{/if}
			</article>
		</div>
	</section>

	<section class="border-base-200 bg-base-100 rounded-3xl border p-6 shadow-sm">
		<AttemptsHistory class="h-[520px]" {quizAttempts} {quizes} {materials} />
	</section>
</div>
