<script lang="ts">
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import { createAttachedFileFromMaterial } from '../new/createAttachedFileFromMaterial';
	import { untrack } from 'svelte';
	import { onMount } from 'svelte';
	import PreviousQuizes from './PreviousQuizes.svelte';
	import { truncateFileName } from '$lib/utils/truncuate-file-name';
	import { createDraft } from '../new/createDraft';
	import Modal from '$lib/ui/Modal.svelte';

	interface Props {
		quizTemplateId: string;

		title: string;
		inputText: string;
		attachedFiles: AttachedFile[];
		selectedDifficulty: string;
		questionCount: number;
		isDraft: boolean;
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

	// states
	let showModal = $state(false);
	let searchQuery = $state('');
	let draftSwitch = $state(true);
	let showDeleteModal = $state(false);
	let draftToDelete: any = $state(null);

	// EFFECTS

	// Title pb update
	$effect(() => {
		const _ = title;
		untrack(() => {
			if (!draftSwitch) {
				pb!.collection('quizes').update(quizTemplateId, { title: title.trim() });
			}
		});
	});

	// Difficulty pb update
	$effect(() => {
		const _ = selectedDifficulty;
		untrack(() => {
			if (!draftSwitch) {
				pb!.collection('quizes').update(quizTemplateId, { difficulty: selectedDifficulty });
			}
		});
	});

	// Question count pb update
	$effect(() => {
		const _ = questionCount;
		untrack(() => {
			if (!draftSwitch) {
				pb!.collection('quizes').update(quizTemplateId, { itemsLimit: questionCount });
			}
		});
	});

	// Input text pb update with debounce
	let debounceTimeout: ReturnType<typeof setTimeout> | undefined;

	$effect(() => {
		const _ = inputText;
		untrack(() => {
			if (!draftSwitch && isDraft && quizTemplateId && inputText) {
				if (debounceTimeout) {
					clearTimeout(debounceTimeout);
				}
				debounceTimeout = setTimeout(() => {
					pb!.collection('quizes').update(quizTemplateId, { query: inputText });
				}, 250);
			}
		});
	});

	// if there are no drafts of this user -> create one. otherwise take the first draft he has
	onMount(() => {
		if (quizesStore.quizes.filter((q) => q.status === 'draft').length == 0) {
			const newDraft = createDraft();
			quizTemplateId = newDraft.id;
			inputText = newDraft.inputText;
			attachedFiles = newDraft.attachedFiles;
			selectedDifficulty = newDraft.selectedDifficulty;
			questionCount = newDraft.questionCount;
			title = newDraft.title;
		} else {
			quizTemplateId = drafts[0].id;
			inputText = drafts[0].query;
			attachedFiles = drafts[0].materials.map((materialId: string) => {
				return createAttachedFileFromMaterial(materialId);
			});
			selectedDifficulty = drafts[0].difficulty;
			questionCount = drafts[0].itemsLimit;
			title = drafts[0].title;
		}

		setTimeout(() => {
			draftSwitch = false;
		}, 0);
	});

	async function handleDraftClick(draft: any) {
		draftSwitch = true;
		quizTemplateId = draft.id;
		inputText = draft.query;
		attachedFiles = draft.materials.map((materialId: string) => {
			return createAttachedFileFromMaterial(materialId);
		});
		selectedDifficulty = draft.difficulty;
		questionCount = draft.itemsLimit;
		title = draft.title;
		setTimeout(() => {
			draftSwitch = false;
		}, 0);
	}

	function isDefaultDraft(draft: any): boolean {
		return (
			draft.query === '' &&
			draft.materials.length === 0 &&
			draft.difficulty === 'intermediate' &&
			draft.itemsLimit === 10 &&
			draft.title.includes('Untitled Quiz')
		);
	}

	async function confirmDelete(draft: any) {
		await pb!.collection('quizes').delete(draft.id);
		quizesStore.quizes = quizesStore.quizes.filter((q) => q.id !== draft.id);
		if (quizTemplateId === draft.id) {
			if (drafts.length > 0) {
				const nextDraft = drafts[0];
				quizTemplateId = nextDraft.id;
				inputText = nextDraft.query;
				attachedFiles = nextDraft.materials.map((materialId: string) => {
					return createAttachedFileFromMaterial(materialId);
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

	async function handleDelete(draft: any) {
		if (isDefaultDraft(draft)) {
			await confirmDelete(draft);
		} else {
			draftToDelete = draft;
			showDeleteModal = true;
		}
	}

	function addEmptyDraft() {
		draftSwitch = true;

		const newDraft = createDraft();
		quizTemplateId = newDraft.id;
		inputText = newDraft.inputText;
		attachedFiles = newDraft.attachedFiles;
		selectedDifficulty = newDraft.selectedDifficulty;
		questionCount = newDraft.questionCount;
		title = newDraft.title;

		setTimeout(() => {
			draftSwitch = false;
		}, 0);
	}
</script>

<div class="mb-0 flex-col w-63">
	<h2 class="mt-0 mb-3 text-center text-3xl font-semibold">Drafts</h2>
	<div class="mt-0 mb-0 flex justify-center">
		<button class="btn btn-xs btn-primary" onclick={addEmptyDraft}>
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
	<div class="mt-2 mb-5 flex justify-center">
		<button class="btn btn-xs btn-secondary" onclick={() => (showModal = true)}>
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
					class="relative cursor-pointer rounded-lg border border-base-200 p-2 shadow-sm transition-shadow hover:shadow-md"
					class:bg-secondary={draft.id === quizTemplateId}
					onclick={() => handleDraftClick(draft)}
					onkeydown={(e) => e.key === 'Enter' && handleDraftClick(draft)}
					role="button"
					tabindex="0"
				>
					<div class="mb-1 truncate font-medium">
						{truncateFileName(draft.title,30)}
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
							class="absolute top-0 right-1 cursor-pointer text-lg text-red-500 hover:text-red-700"
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
	<Modal open={showModal} onclose={() => showModal = false} class="max-h-screen max-w-sm items-start">
		<h3 class="text-center text-xl font-bold">Create draft from a previous quiz</h3>
		<div class="relative mt-4 mb-4">
			<input
				bind:value={searchQuery}
				placeholder="Search previous quizes.."
				class="w-full rounded border border-base-300 py-1 pr-2 pl-8 text-sm focus:border-primary focus:outline-none"
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
				class="lucide lucide-search absolute top-1/2 left-2 -translate-y-1/2 transform text-base-content/60"
				><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg
			>
		</div>
		<div class="flex max-h-135 justify-start overflow-y-auto">
			<PreviousQuizes
				bind:quizTemplateId
				bind:title
				bind:inputText
				bind:attachedFiles
				bind:selectedDifficulty
				bind:questionCount
				bind:draftSwitch
				{searchQuery}
				onQuizSelected={() => (showModal = false)}
			/>
		</div>
	</Modal>
{/if}

{#if showDeleteModal}
	<Modal open={showDeleteModal} onclose={() => showDeleteModal = false}>
		<p>Are you sure you want to delete this draft?</p>
		<div class="flex justify-end gap-2 mt-4">
			<button class="btn btn-ghost" onclick={() => showDeleteModal = false}>No</button>
			<button class="btn btn-error" onclick={() => { confirmDelete(draftToDelete); showDeleteModal = false; }}>Yes</button>
		</div>
	</Modal>
{/if}
