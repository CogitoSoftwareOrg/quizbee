<script lang="ts">
	import { Search, Filter, BookOpen, Clock, FileText, Crown, Loader2 } from 'lucide-svelte';

	import { Input, Button } from '@quizbee/ui-svelte-daisy';

	import type {
		MaterialsResponse,
		QuizesResponse,
		QuizExpand,
		QuizItemsResponse,
		QuizAttemptsResponse,
		QuizAttemptExpand
	} from '$lib/pb';

	import type { ClassValue } from 'svelte/elements';
	import { quizItemsStore } from './quizItems.svelte';
	import { quizesStore } from './quizes.svelte';

	interface QuizItem {
		quizId: string;
		title: string;
		summary: string;
		difficulty: string;
		status: string;
		visibility: string;
		tags: string[];
		created: string;
		updated: string;
		materials: string[];
		questionsCount: number;
		attemptsCount: number;
		lastAttemptDate: string;
		isAuthor: boolean;
		isInProgress: boolean;
	}

	interface Props {
		class?: ClassValue;
		quizAttempts: QuizAttemptsResponse[];
		materials: MaterialsResponse[];
		userId: string;
	}

	const { class: className = '', quizAttempts, materials, userId }: Props = $props();

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

	const quizList: QuizItem[] = $derived.by(() => {
		const materialMap = new Map(materials.map((material) => [material.id, material.title]));

		// Group all attempts by quiz ID
		const quizAttemptsMap = new Map<string, QuizAttemptsResponse[]>();

		for (const attempt of quizAttempts) {
			const quizId = attempt.quiz;
			if (!quizAttemptsMap.has(quizId)) {
				quizAttemptsMap.set(quizId, []);
			}
			quizAttemptsMap.get(quizId)!.push(attempt);
		}

		// Extract unique quizzes from all attempts
		const uniqueQuizzes = new Map<string, QuizesResponse<QuizExpand>>();

		// Create a map of user's quizzes from store for quick lookup
		const userQuizzesMap = new Map(quizesStore.quizes.map((quiz) => [quiz.id, quiz]));

		for (const attempt of quizAttempts) {
			const quiz = (attempt.expand as QuizAttemptExpand)?.quiz;
			if (quiz && !uniqueQuizzes.has(quiz.id)) {
				// Use reactive quiz from store if it's user's quiz, otherwise use expanded quiz
				const quizToUse = quiz.author === userId ? userQuizzesMap.get(quiz.id) || quiz : quiz;
				uniqueQuizzes.set(quiz.id, quizToUse);
			}
		}

		// Create quiz items from unique quizzes
		const items = Array.from(uniqueQuizzes.values()).map((quiz) => {
			const quizItems =
				(quizItemsStore.quizItemsMap.get(quiz.id) as QuizItemsResponse[]) ||
				((quiz.expand as QuizExpand)?.quizItems_via_quiz as QuizItemsResponse[]) ||
				[];

			const attempts = quizAttemptsMap.get(quiz.id) || [];
			const isAuthor = quiz.author === userId;

			// Check if this quiz is in progress:
			// - Quiz status is 'creating', OR
			// - Has at least one attempt without feedback
			const isInProgress = quiz.status === 'creating' || attempts.some((a) => !a.feedback);

			// Materials only for author's quizzes
			const materialTitles = isAuthor
				? (quiz.materials || [])
						.map((id) => materialMap.get(id))
						.filter((title): title is string => Boolean(title))
				: [];

			const tags = Array.isArray(quiz.tags) ? (quiz.tags as string[]) : [];

			// Find last attempt date
			const lastAttempt = attempts.toSorted((a, b) => b.updated.localeCompare(a.updated))[0];
			const lastAttemptDate = lastAttempt?.updated || quiz.updated;

			return {
				quizId: quiz.id,
				title: quiz.title || 'Untitled quiz',
				summary: quiz.summary || '',
				difficulty: quiz.difficulty || 'intermediate',
				status: quiz.status || 'draft',
				visibility: quiz.visibility || 'private',
				tags,
				created: quiz.created,
				updated: quiz.updated,
				materials: materialTitles,
				questionsCount: quizItems.length,
				attemptsCount: attempts.length,
				lastAttemptDate,
				isAuthor,
				isInProgress
			} satisfies QuizItem;
		});

		// Sort by last attempt date (most recent first)
		return items.toSorted((a, b) => b.lastAttemptDate.localeCompare(a.lastAttemptDate));
	});

	// Filter state
	let searchQuery = $state('');
	let selectedDifficulties = $state<string[]>([]);
	let selectedOwnership = $state<'all' | 'mine' | 'others'>('all');
	let showInProgress = $state(true);
	let showFilters = $state(false);

	const filteredQuizes = $derived.by(() => {
		const search = searchQuery.trim().toLowerCase();
		let result = quizList;

		// In-progress filter
		if (!showInProgress) {
			result = result.filter((item) => !item.isInProgress);
		}

		// Search filter
		if (search) {
			result = result.filter((item) => {
				if (item.title.toLowerCase().includes(search)) return true;
				if (item.summary.toLowerCase().includes(search)) return true;
				if (item.materials.some((mat) => mat.toLowerCase().includes(search))) return true;
				if (item.tags.some((tag) => tag.toLowerCase().includes(search))) return true;
				return false;
			});
		}

		// Difficulty filter (multiple choice)
		if (selectedDifficulties.length > 0) {
			result = result.filter((item) => selectedDifficulties.includes(item.difficulty));
		}

		// Ownership filter
		if (selectedOwnership === 'mine') {
			result = result.filter((item) => item.isAuthor);
		} else if (selectedOwnership === 'others') {
			result = result.filter((item) => !item.isAuthor);
		}

		return result.toSorted((a, b) => b.lastAttemptDate.localeCompare(a.lastAttemptDate));
	});

	const difficultyColors: Record<string, string> = {
		beginner: 'badge-success',
		intermediate: 'badge-warning',
		expert: 'badge-error'
	};

	function resetFilters() {
		searchQuery = '';
		selectedDifficulties = [];
		selectedOwnership = 'all';
		showInProgress = true;
	}

	function toggleDifficulty(difficulty: string) {
		if (selectedDifficulties.includes(difficulty)) {
			selectedDifficulties = selectedDifficulties.filter((d) => d !== difficulty);
		} else {
			selectedDifficulties = [...selectedDifficulties, difficulty];
		}
	}

	const hasActiveFilters = $derived(
		searchQuery || selectedDifficulties.length > 0 || selectedOwnership !== 'all' || !showInProgress
	);
</script>

<div class={['flex h-full flex-col gap-6 overflow-y-auto md:overflow-y-visible', className]}>
	<header class="flex shrink-0 flex-col gap-3">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-3xl font-semibold tracking-tight">My Quizes</h1>
				<p class="text-base-content/70 mt-1 text-sm">
					View all quizzes you've attempted, sorted by most recent activity.
				</p>
			</div>
		</div>

		<div class="flex flex-col gap-3 sm:flex-row">
			<Input
				class="w-full flex-1"
				placeholder="Search by title, summary, materials, or tags"
				value={searchQuery}
				oninput={(event) => {
					const target = event.target as HTMLInputElement;
					searchQuery = target.value;
				}}
			>
				{#snippet children()}
					<Search class="opacity-50" size={18} />
				{/snippet}
			</Input>

			<Button
				color={showFilters || hasActiveFilters ? 'primary' : 'neutral'}
				style={showFilters || hasActiveFilters ? 'solid' : 'outline'}
				onclick={() => (showFilters = !showFilters)}
				class="sm:w-auto"
			>
				<Filter size={18} />
				Filters
				{#if hasActiveFilters && !showFilters}
					<span class="badge badge-sm">•</span>
				{/if}
			</Button>
		</div>

		{#if showFilters}
			<div class="bg-base-200/50 border-base-300 flex flex-col gap-5 rounded-xl border p-5">
				<!-- In Progress Filter -->
				<div class="flex flex-col gap-2">
					<span class="label-text font-medium">Show in progress</span>
					<div class="flex flex-wrap gap-2">
						<Button
							size="sm"
							color={showInProgress ? 'primary' : 'neutral'}
							style={showInProgress ? 'solid' : 'outline'}
							onclick={() => (showInProgress = true)}
						>
							<Loader2 size={14} />
							Show In Progress
						</Button>
						<Button
							size="sm"
							color={!showInProgress ? 'primary' : 'neutral'}
							style={!showInProgress ? 'solid' : 'outline'}
							onclick={() => (showInProgress = false)}
						>
							Hide In Progress
						</Button>
					</div>
				</div>

				<!-- Ownership Filter -->
				<div class="flex flex-col gap-2">
					<span class="label-text font-medium">Quiz ownership</span>
					<div class="flex flex-wrap gap-2">
						<Button
							size="sm"
							color={selectedOwnership === 'all' ? 'primary' : 'neutral'}
							style={selectedOwnership === 'all' ? 'solid' : 'outline'}
							onclick={() => (selectedOwnership = 'all')}
						>
							All Quizzes
						</Button>
						<Button
							size="sm"
							color={selectedOwnership === 'mine' ? 'accent' : 'neutral'}
							style={selectedOwnership === 'mine' ? 'solid' : 'outline'}
							onclick={() => (selectedOwnership = 'mine')}
						>
							<Crown size={14} />
							My Quizzes
						</Button>
						<Button
							size="sm"
							color={selectedOwnership === 'others' ? 'neutral' : 'neutral'}
							style={selectedOwnership === 'others' ? 'solid' : 'outline'}
							onclick={() => (selectedOwnership = 'others')}
						>
							Other Quizzes
						</Button>
					</div>
				</div>

				<!-- Difficulty Filter -->
				<div class="flex flex-col gap-2">
					<span class="label-text font-medium">Difficulty (multiple choice)</span>
					<div class="flex flex-wrap gap-2">
						<Button
							size="sm"
							color={selectedDifficulties.includes('beginner') ? 'success' : 'neutral'}
							style={selectedDifficulties.includes('beginner') ? 'solid' : 'outline'}
							onclick={() => toggleDifficulty('beginner')}
						>
							Beginner
						</Button>
						<Button
							size="sm"
							color={selectedDifficulties.includes('intermediate') ? 'info' : 'neutral'}
							style={selectedDifficulties.includes('intermediate') ? 'solid' : 'outline'}
							onclick={() => toggleDifficulty('intermediate')}
						>
							Intermediate
						</Button>
						<Button
							size="sm"
							color={selectedDifficulties.includes('expert') ? 'error' : 'neutral'}
							style={selectedDifficulties.includes('expert') ? 'solid' : 'outline'}
							onclick={() => toggleDifficulty('expert')}
						>
							Expert
						</Button>
					</div>
				</div>

				{#if hasActiveFilters}
					<div class="border-base-300 flex justify-end border-t pt-3">
						<Button size="sm" style="ghost" onclick={resetFilters}>Reset all filters</Button>
					</div>
				{/if}
			</div>
		{/if}
	</header>

	<section class="-ml-5 flex flex-col gap-4 md:min-h-0 md:flex-1">
		{#if filteredQuizes.length === 0}
			<div
				class="border-base-200 bg-base-100 flex flex-col items-center gap-3 rounded-xl border p-8 text-center shadow-sm"
			>
				{#if hasActiveFilters}
					<Search class="opacity-40" size={48} />
					<div>
						<p class="font-medium">No quizzes match your search</p>
						<p class="text-base-content/70 text-sm">
							Adjust the keywords or clear the filters to see more results.
						</p>
					</div>
					<Button size="sm" onclick={resetFilters}>Clear filters</Button>
				{:else}
					<BookOpen class="opacity-40" size={48} />
					<div>
						<p class="font-medium">No quizzes yet</p>
						<p class="text-base-content/70 text-sm">Create your first quiz to get started.</p>
					</div>
				{/if}
			</div>
		{:else}
			<!-- Make only the quiz list scrollable on desktop -->
			<ul class="grid gap-4 py-2 pr-1 md:overflow-y-auto">
				{#each filteredQuizes as item}
					<li>
						<a
							class={[
								'group flex flex-col gap-4 rounded-xl border p-5 no-underline shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2',
								item.isInProgress
									? 'border-primary/50 bg-primary/5 hover:bg-primary/10'
									: 'border-base-200 hover:bg-base-200/60 bg-base-100'
							]}
							href={`/quizes/${item.quizId}`}
						>
							<div class="flex flex-wrap items-start justify-between gap-3">
								<div class="flex-1">
									<p
										class={[
											'text-lg font-semibold leading-tight transition',
											item.isInProgress
												? 'group-hover:text-primary text-primary'
												: 'group-hover:text-primary'
										]}
									>
										{item.title}
									</p>
									{#if item.summary}
										<p class="text-base-content/60 mt-1 text-sm leading-relaxed">
											{item.summary.slice(0, 500)}...
										</p>
									{/if}
									<div class="text-base-content/70 mt-2 flex items-center gap-2 text-xs">
										<Clock size={12} class="opacity-60" />
										<span>Last attempt: {formatDateTime(item.lastAttemptDate)}</span>
									</div>
								</div>
							</div>

							<div class="flex flex-wrap items-center gap-2">
								<!-- In Progress badge -->
								{#if item.isInProgress}
									<span class="badge badge-primary"> In Progress </span>
								{/if}

								<!-- Author badge -->
								{#if item.isAuthor}
									<span class="badge badge-accent">
										<Crown size={12} />
										My Quiz
									</span>
								{/if}

								<!-- Difficulty -->
								<span class={['badge', difficultyColors[item.difficulty] || 'badge-ghost']}>
									{item.difficulty.charAt(0).toUpperCase() + item.difficulty.slice(1)}
								</span>

								<!-- Questions count -->
								{#if item.questionsCount > 0}
									<span class="badge badge-outline">
										<FileText size={12} />
										{item.questionsCount}
										{item.questionsCount === 1 ? 'question' : 'questions'}
									</span>
								{/if}

								<!-- Attempts count -->
								{#if item.attemptsCount > 0}
									<span class="badge badge-outline">
										<Clock size={12} />
										{item.attemptsCount}
										{item.attemptsCount === 1 ? 'attempt' : 'attempts'}
									</span>
								{/if}
							</div>

							<!-- Materials -->
							{#if item.materials.length > 0}
								<div class="flex flex-wrap gap-2">
									{#each item.materials as material}
										<span class="badge badge-soft badge-primary text-xs" title={material}>
											{material}
										</span>
									{/each}
								</div>
							{/if}

							<!-- Tags -->
							{#if item.tags.length > 0}
								<div class="flex flex-wrap gap-2">
									{#each item.tags as tag}
										<span class="badge badge-soft text-xs">#{tag}</span>
									{/each}
								</div>
							{/if}
						</a>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
</div>
