<script lang="ts">
	import { Clock, Search } from 'lucide-svelte';

	import type { Answer } from '$lib/apps/quizes/types';
	import type {
		MaterialsResponse,
		QuizAttemptsResponse,
		QuizesResponse,
		QuizExpand,
		QuizItemsResponse
	} from '$lib/pb';
	import Input from '$lib/ui/Input.svelte';

	import type { Decision } from './types';
	import type { ClassValue } from 'svelte/elements';
	interface HistoryPoint {
		quizId: string;
		attemptId: string;
		title: string;
		created: string;
		updated: string;
		materials: string[];
		correctCount: number;
		totalCount: number;
		answerTexts: string[];
	}

	interface Props {
		class?: ClassValue;
		quizAttempts: QuizAttemptsResponse[];
		quizes: QuizesResponse<QuizExpand>[];
		materials: MaterialsResponse[];
	}

	const { class: className = '', quizAttempts, quizes, materials }: Props = $props();

	function ensureAnswersArray(answers: unknown): Answer[] {
		if (!answers) return [];
		if (typeof answers === 'string') {
			try {
				const parsed = JSON.parse(answers);
				return Array.isArray(parsed) ? (parsed as Answer[]) : [];
			} catch (error) {
				return [];
			}
		}
		return (answers as Answer[]) || [];
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

	const history: HistoryPoint[] = $derived.by(() => {
		const materialMap = new Map(materials.map((material) => [material.id, material.title]));

		const entries = quizAttempts
			.filter((attempt) => Boolean(attempt.feedback))
			.map((attempt) => {
				const quiz = quizes.find((candidate) => candidate.id === attempt.quiz)!;

				const decisions = (attempt.choices as Decision[]) || [];
				const totalCount = decisions.length;
				const correctCount = decisions.filter((decision) => decision.correct).length;

				const quizItems = (quiz.expand?.quizItems_via_quiz || []) as QuizItemsResponse[];
				const answerTexts = quizItems.flatMap((item) => {
					const answers = ensureAnswersArray(item.answers);
					return answers.map((answer) => answer.content || '');
				});

				const materialTitles = quiz.materials
					.map((id) => materialMap.get(id))
					.filter((title): title is string => Boolean(title));

				return {
					quizId: quiz.id,
					attemptId: attempt.id,
					title: quiz.title || 'Untitled quiz',
					created: attempt.created,
					updated: attempt.updated,
					materials: materialTitles,
					correctCount,
					totalCount,
					answerTexts
				} satisfies HistoryPoint;
			});

		return entries.toSorted((a, b) => b.updated.localeCompare(a.updated));
	});

	let searchQuery = $state('');

	// Дублируем history 100 раз для тестирования интерфейса
	// const testHistory = $derived.by(() => {
	// 	let arr: HistoryPoint[] = [];
	// 	for (let i = 0; i < 100; i++) {
	// 		arr = arr.concat(history);
	// 	}
	// 	return arr;
	// });

	const filteredHistory = $derived.by(() => {
		const search = searchQuery.trim().toLowerCase();
		if (!search) return history;

		return history.filter((item) => {
			if (item.title.toLowerCase().includes(search)) return true;
			return item.answerTexts.some((answer) => answer.toLowerCase().includes(search));
		});
	});
</script>

<div class={['flex h-full flex-col gap-6', className]}>
	<header class="flex flex-col gap-2">
		<h1 class="text-3xl font-semibold tracking-tight">Quiz history</h1>
		<p class="text-base-content/70 text-sm">
			Review every completed attempt, revisit materials, and drill into detailed feedback.
		</p>
		<Input
			class="w-full max-w-xl"
			placeholder="Search by quiz title or answers"
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
	</header>

	<section class="flex min-h-0 flex-1 flex-col gap-4">
		{#if filteredHistory.length === 0}
			<div
				class="border-base-200 bg-base-100 flex flex-col items-center gap-3 rounded-xl border px-6 text-center shadow-sm"
			>
				<Search class="opacity-40" size={32} />
				<div>
					<p class="font-medium">No attempts match your search</p>
					<p class="text-base-content/70 text-sm">Adjust the keywords or clear the filter.</p>
				</div>
			</div>
		{:else}
			<!-- Make only the history list scrollable -->
			<ul class="grid flex-1 gap-4 overflow-y-auto py-4 pr-1">
				{#each filteredHistory as item}
					{@const incorrectCount = item.totalCount - item.correctCount}
					<li>
						<a
							class="border-base-200 hover:bg-base-200/60 bg-base-100 group flex flex-col gap-4 rounded-xl border p-5 no-underline shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2"
							href={`/quizes/${item.quizId}/attempts/${item.attemptId}/feedback`}
						>
							<div class="flex flex-wrap items-start justify-between gap-3">
								<div>
									<p
										class="group-hover:text-primary text-lg font-semibold leading-tight transition"
									>
										{item.title}
									</p>
									<div class="text-base-content/70 flex items-center gap-2 text-sm">
										<Clock size={14} class="opacity-60" />
										<span>{formatDateTime(item.updated)}</span>
									</div>
								</div>
								<div class="flex flex-wrap items-center gap-2">
									<span class="badge badge-primary badge-lg">
										{item.correctCount} / {item.totalCount}
									</span>
								</div>
							</div>

							{#if item.materials.length > 0}
								<div class="flex flex-wrap gap-2">
									{#each item.materials as material}
										<span class="badge badge-outline" title={material}>
											{material}
										</span>
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
