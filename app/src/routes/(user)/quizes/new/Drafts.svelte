<script lang="ts">
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import { createAttachedFileFromMaterial } from '../new/createAttachedFileFromMaterial';
	import { generateId } from '$lib/utils/generate-id';
	import { untrack } from 'svelte';
	import { onMount } from 'svelte';
	import PreviousQuizes from './PreviousQuizes.svelte';

	function generateUniqueTitle(baseTitle: string, existingTitles: string[]): string {
		let title = baseTitle;
		let counter = 1;
		while (existingTitles.includes(title)) {
			title = `${baseTitle} (${counter})`;
			counter++;
		}
		return title;
	}

	function truncateFileName(filename: string, maxLength: number = 50): string {
		if (filename.length <= maxLength) {
			return filename;
		}
		return filename.substring(0, maxLength - 3) + '...';
	}

	interface Props {
		quizTemplateId: string;

		title: string;
		inputText: string;
		attachedFiles: AttachedFile[];
		selectedDifficulty: string;
		questionCount: number;
		isDraft: boolean;
	}

	async function createDraftFromCurrent() {
		const currentQuiz = quizesStore.quizes.find((q) => q.id === quizTemplateId);
		if (!currentQuiz) return;

		const newId = generateId();
		const formData = new FormData();
		formData.append('status', 'draft');
		formData.append('query', inputText);
		formData.append('materials', JSON.stringify(currentQuiz.materials || []));
		formData.append('difficulty', selectedDifficulty);
		formData.append('itemsLimit', questionCount.toString());
		formData.append('author', pb!.authStore.model?.id || '');
		const baseTitle = `Draft from ${currentQuiz.title || 'Quiz'}`;
		const existingTitles = drafts.map((d) => d.title);
		const uniqueTitle = generateUniqueTitle(baseTitle, existingTitles);
		formData.append('title', uniqueTitle);
		formData.append('id', newId);

		pb!.collection('quizes').create(formData);
		quizTemplateId = newId;
		title = uniqueTitle;
	}

	let {
		title = $bindable(),
		quizTemplateId = $bindable(),
		inputText = $bindable(),
		attachedFiles = $bindable(),
		selectedDifficulty = $bindable(),
		questionCount = $bindable(),
		isDraft = $bindable()
	}: Props = $props();

	// drafts from store
	const drafts = $derived(quizesStore.quizes.filter((q: any) => q.status === 'draft'));

	let showModal = $state(false);
	let searchQuery = $state('');
	let isAddingDraft = false;
	$effect(() => {
		const d = selectedDifficulty;
		untrack(() => {
			if (isAddingDraft && isDraft && quizTemplateId && d) {
				pb!.collection('quizes').update(quizTemplateId, { difficulty: d });
			}
		});
	});

	// Автоматическое обновление количества вопросов в PB
	$effect(() => {
		if (
			!untrack(() => isAddingDraft) &&
			untrack(() => isDraft) &&
			untrack(() => quizTemplateId) &&
			questionCount
		) {
			pb!.collection('quizes').update(
				untrack(() => quizTemplateId),
				{ itemsLimit: questionCount }
			);
		}
	});

	let debounceTimeout: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		if (
			!untrack(() => isAddingDraft) &&
			untrack(() => isDraft) &&
			untrack(() => quizTemplateId) &&
			inputText
		) {
			if (debounceTimeout) {
				clearTimeout(debounceTimeout);
			}
			debounceTimeout = setTimeout(() => {
				pb!.collection('quizes').update(
					untrack(() => quizTemplateId),
					{ query: inputText }
				);
			}, 750);
		}
	});

	$effect(() => {
		[inputText, attachedFiles, selectedDifficulty, questionCount];
		const newId = generateId();
		if (!isDraft) {
			createDraftFromCurrent();

			setTimeout(() => {
				isDraft = true;
			}, 0);
		}
	});

	// if there are no drafts of this user -> create one. otherwise take the first draft he has
	onMount(() => {
		if (quizesStore.quizes.filter((q) => q.status === 'draft').length == 0) {
			addDraft();
		} else {
			quizTemplateId = drafts[0].id;
			inputText = drafts[0].query;
			attachedFiles = drafts[0].materials.map((materialId: string) => {
				return createAttachedFileFromMaterial(materialId, drafts[0].status);
			});
			selectedDifficulty = drafts[0].difficulty;
			questionCount = drafts[0].itemsLimit;
			title = drafts[0].title;
		}
	});

	async function handleDraftClick(draft: any) {
		quizTemplateId = draft.id;
		inputText = draft.query;
		attachedFiles = draft.materials.map((materialId: string) => {
			return createAttachedFileFromMaterial(materialId, draft.status);
		});
		selectedDifficulty = draft.difficulty;
		questionCount = draft.itemsLimit;
		title = draft.title;
	}

	async function handleDelete(draft: any) {
		if (confirm('Are you sure you want to delete this draft?')) {
			await pb!.collection('quizes').delete(draft.id);
			quizesStore.quizes = quizesStore.quizes.filter((q) => q.id !== draft.id);
			if (quizTemplateId === draft.id) {
				if (drafts.length > 0) {
					const nextDraft = drafts[0];
					quizTemplateId = nextDraft.id;
					inputText = nextDraft.query;
					attachedFiles = nextDraft.materials.map((materialId: string) => {
						return createAttachedFileFromMaterial(materialId, nextDraft.status);
					});
					selectedDifficulty = nextDraft.difficulty;
					questionCount = nextDraft.itemsLimit;
					title = nextDraft.title;
				} else {
					quizTemplateId = '';
					inputText = '';
					attachedFiles = [];
					selectedDifficulty = 'intermediate';
					questionCount = 10;
					title = '';
				}
			}
		}
	}

	async function addDraft() {
		isAddingDraft = true;

		const newId = generateId();
		const formData = new FormData();
		formData.append('status', 'draft');
		formData.append('query', '');
		formData.append('attachedFiles', JSON.stringify([]));
		formData.append('difficulty', 'intermediate');
		formData.append('questionCount', '10');
		formData.append('author', pb!.authStore.model?.id || '');
		const baseTitle = 'Draft';
		const existingTitles = drafts.map((d) => d.title);
		const uniqueTitle = generateUniqueTitle(baseTitle, existingTitles);
		formData.append('title', uniqueTitle);
		formData.append('id', newId);

		pb!.collection('quizes').create(formData);

		quizTemplateId = newId;
		inputText = '';
		attachedFiles = [];
		selectedDifficulty = 'intermediate';
		questionCount = 10;
		title = uniqueTitle;

		setTimeout(() => {
			isAddingDraft = false;
		}, 0);
	}
</script>

<div class="mb-0">
	<h2 class="mb-3 mt-0 text-center text-3xl font-semibold">Drafts</h2>
	<div class="mb-0 mt-0 flex justify-center">
		<button class="btn btn-primary btn-xs" onclick={addDraft}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="3"
				stroke-linecap="round"
				stroke-linejoin="round"
				class="lucide lucide-plus mr-1"><path d="M12 5v14M5 12h14" /></svg
			>
			<span class="mt-1 text-[0.8rem]">Add Empty Draft</span>
		</button>
	</div>
	<div class="mb-5 mt-2 flex justify-center">
		<button class="btn btn-secondary btn-xs" onclick={() => (showModal = true)}>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				width="16"
				height="16"
				viewBox="0 0 24 24"
				fill="none"
				stroke="currentColor"
				stroke-width="3"
				stroke-linecap="round"
				stroke-linejoin="round"
				class="lucide lucide-plus mr-1"><path d="M12 5v14M5 12h14" /></svg
			>
			<span class="mt-1 text-[0.8rem]">Create from a Quiz</span>
		</button>
	</div>
	{#if drafts.length === 0}
		<div class="text-center">
			<p class="text-sm">No drafts yet</p>
			<p class="mt-1 text-xs">Start drafting your quiz and it will appear here.</p>
		</div>
	{:else}
		<div class="max-h-150 space-y-3 overflow-y-auto">
			{#each drafts as draft}
				<div
					class="border-base-200 relative cursor-pointer rounded-lg border p-2 shadow-sm transition-shadow hover:shadow-md"
					class:bg-yellow-100={draft.id === quizTemplateId}
					onclick={() => handleDraftClick(draft)}
					onkeydown={(e) => e.key === 'Enter' && handleDraftClick(draft)}
					role="button"
					tabindex="0"
				>
					<div class="mb-1 truncate font-medium">
						{truncateFileName(draft.title, 28)}
					</div>
					<div class="text-muted text-xs">
						{#if draft.updated}
							Last updated: {new Date(draft.updated).toLocaleString()}
						{:else}
							Created: {new Date(draft.created).toLocaleString()}
						{/if}
					</div>
					{#if drafts.length > 1}
						<button
							class="absolute right-0 top-0 cursor-pointer text-lg text-red-500 hover:text-red-700"
							onclick={(e) => {
								e.stopPropagation();
								handleDelete(draft);
							}}
							title="Delete draft"
						>
							&times;
						</button>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if showModal}
	<div class="modal modal-open">
		<div class="modal-box relative max-h-screen max-w-sm items-start">
			<button
				class="btn btn-sm btn-circle btn-ghost absolute right-1 top-1 text-xl"
				onclick={() => (showModal = false)}>&times;</button
			>
			<h3 class="text-center text-xl font-bold">Create draft from a previous quiz</h3>
			<div class="relative mb-4 mt-4">
				<input
					bind:value={searchQuery}
					placeholder="Search previous quizes.."
					class="border-base-300 focus:border-primary w-full rounded border py-1 pl-8 pr-2 text-sm focus:outline-none"
				/>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="2"
					stroke-linecap="round"
					stroke-linejoin="round"
					class="text-base-content/60 lucide lucide-search absolute left-2 top-1/2 -translate-y-1/2 transform"
					><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg
				>
			</div>
			<div class="max-h-135 flex justify-start overflow-y-auto">
				<PreviousQuizes
					bind:searchQuery
					bind:quizTemplateId
					bind:inputText
					bind:attachedFiles
					bind:selectedDifficulty
					bind:questionCount
					bind:isDraft
					onQuizSelected={() => (showModal = false)}
				/>
			</div>
		</div>
	</div>
{/if}
