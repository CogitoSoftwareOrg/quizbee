<script lang="ts">
	import { Search, Filter, BookOpen, Clock, FileText } from 'lucide-svelte';

	import { Input, Button } from '@cogisoft/ui-svelte-daisy';

	import type { MaterialsResponse, QuizesResponse, QuizExpand, QuizItemsResponse } from '$lib/pb';

	import type { ClassValue } from 'svelte/elements';
	import { quizItemsStore } from './quizItems.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';

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
	}

	interface Props {
		class?: ClassValue;
		quizes: QuizesResponse<QuizExpand>[];
		materials: MaterialsResponse[];
	}

	const { class: className = '', quizes, materials }: Props = $props();

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

		return quizes.map((quiz) => {
			const quizItems =
				(quizItemsStore.quizItemsMap.get(quiz.id) as QuizItemsResponse[]) ||
				((quiz.expand as QuizExpand)?.quizItems_via_quiz as QuizItemsResponse[]) ||
				[];

			const attempts = quizAttemptsStore.quizAttempts.filter((attempt) => attempt.quiz === quiz.id);

			const materialTitles = (quiz.materials || [])
				.map((id) => materialMap.get(id))
				.filter((title): title is string => Boolean(title));

			const tags = Array.isArray(quiz.tags) ? (quiz.tags as string[]) : [];

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
				attemptsCount: attempts.length
			} satisfies QuizItem;
		});
	});

	// Filter state
	let searchQuery = $state('');
	let selectedDifficulty = $state<string>('all');
	let selectedStatus = $state<string>('all');
	let showFilters = $state(false);

	const filteredQuizes = $derived.by(() => {
		const search = searchQuery.trim().toLowerCase();
		let result = quizList;

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

		// Difficulty filter
		if (selectedDifficulty !== 'all') {
			result = result.filter((item) => item.difficulty === selectedDifficulty);
		}

		// Status filter
		if (selectedStatus !== 'all') {
			result = result.filter((item) => item.status === selectedStatus);
		}

		return result.toSorted((a, b) => b.updated.localeCompare(a.updated));
	});

	const difficultyColors: Record<string, string> = {
		easy: 'badge-success',
		intermediate: 'badge-info',
		hard: 'badge-warning',
		expert: 'badge-error'
	};

	const statusColors: Record<string, string> = {
		draft: 'badge-ghost',
		ready: 'badge-info',
		public: 'badge-success',
		search: 'badge-primary'
	};

	function resetFilters() {
		searchQuery = '';
		selectedDifficulty = 'all';
		selectedStatus = 'all';
	}

	const hasActiveFilters = $derived(
		searchQuery || selectedDifficulty !== 'all' || selectedStatus !== 'all'
	);
</script>

<div class={['flex h-full flex-col gap-6', className]}>
	<header class="flex flex-col gap-3">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-3xl font-semibold tracking-tight">My Quizes</h1>
				<p class="text-base-content/70 mt-1 text-sm">
					Create, manage, and share your custom quizzes.
				</p>
			</div>
		</div>

		<div class="flex flex-col gap-3 sm:flex-row">
			<Input
				class="flex-1"
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
			<div class="bg-base-200/50 border-base-300 flex flex-col gap-4 rounded-xl border p-4">
				<div class="grid gap-4 sm:grid-cols-2">
					<div>
						<label class="label" for="difficulty-select">
							<span class="label-text font-medium">Difficulty</span>
						</label>
						<select
							id="difficulty-select"
							class="select select-bordered w-full"
							bind:value={selectedDifficulty}
							onchange={() => {}}
						>
							<option value="all">All difficulties</option>
							<option value="easy">Easy</option>
							<option value="intermediate">Intermediate</option>
							<option value="hard">Hard</option>
							<option value="expert">Expert</option>
						</select>
					</div>

					<div>
						<label class="label" for="status-select">
							<span class="label-text font-medium">Status</span>
						</label>
						<select
							id="status-select"
							class="select select-bordered w-full"
							bind:value={selectedStatus}
							onchange={() => {}}
						>
							<option value="all">All statuses</option>
							<option value="draft">Draft</option>
							<option value="ready">Ready</option>
							<option value="public">Public</option>
							<option value="search">Search</option>
						</select>
					</div>
				</div>

				{#if hasActiveFilters}
					<div class="flex justify-end">
						<Button size="sm" style="ghost" onclick={resetFilters}>Reset filters</Button>
					</div>
				{/if}
			</div>
		{/if}
	</header>

	<section class="flex min-h-0 flex-1 flex-col gap-4">
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
			<!-- Make only the quiz list scrollable -->
			<ul class="grid gap-4 overflow-y-auto py-2 pr-1">
				{#each filteredQuizes as item}
					<li>
						<a
							class="border-base-200 hover:bg-base-200/60 bg-base-100 group flex flex-col gap-4 rounded-xl border p-5 no-underline shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
							href={`/quizes/${item.quizId}`}
						>
							<div class="flex flex-wrap items-start justify-between gap-3">
								<div class="flex-1">
									<p
										class="group-hover:text-primary text-lg font-semibold leading-tight transition"
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
										<span>{formatDateTime(item.updated)}</span>
									</div>
								</div>
							</div>

							<div class="flex flex-wrap items-center gap-2">
								<!-- Difficulty -->
								<span class={['badge', difficultyColors[item.difficulty] || 'badge-ghost']}>
									{item.difficulty.charAt(0).toUpperCase() + item.difficulty.slice(1)}
								</span>

								<!-- Status -->
								<span class={['badge', statusColors[item.status] || 'badge-ghost']}>
									{item.status.charAt(0).toUpperCase() + item.status.slice(1)}
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
