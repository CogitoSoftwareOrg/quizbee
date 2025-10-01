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
	import Button from '$lib/ui/Button.svelte';
	import { Plus } from 'lucide-svelte';

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

<div class="border-base-200 flex w-64 flex-shrink-0 flex-col border-r">
	<header class="border-base-300 space-y-1 border-b px-4 py-3">
		<h2 class="mb-4 text-center text-3xl font-semibold">Drafts</h2>
		<div class="flex justify-center">
			<Button style="outline" size="sm" block onclick={addEmptyDraft}>
				<Plus size={20} />
				<span class="text-lg">Add Empty Draft </span>
			</Button>
		</div>
		<div class="flex justify-center">
			<Button color="secondary" style="outline" size="sm" block onclick={() => (showModal = true)}>
				<Plus size={20} />
				<span class="text-lg">Create from a Quiz</span>
			</Button>
		</div>
	</header>
	{#if drafts.length === 0}
		<div class="px-4 text-center">
			<p class="text-sm">No drafts yet</p>
			<p class="mt-1 text-xs">Start drafting your quiz and it will appear here.</p>
		</div>
	{:else}
		<div class="max-h-150 mt-2 space-y-3 overflow-y-auto px-4">
			{#each drafts as draft}
				<div
					class={[
						'border-base-200 relative cursor-pointer rounded-lg border p-2 shadow-sm transition-shadow hover:shadow-md',
						draft.id === quizTemplateId && 'border-primary border-2'
					]}
					onclick={() => handleDraftClick(draft)}
					onkeydown={(e) => e.key === 'Enter' && handleDraftClick(draft)}
					role="button"
					tabindex="0"
				>
					<div class="mb-1 truncate font-medium">
						{truncateFileName(draft.title, 30)}
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
							class="absolute right-1 top-0 cursor-pointer text-lg text-red-500 hover:text-red-700"
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
	<Modal
		open={showModal}
		onclose={() => (showModal = false)}
		class="max-h-screen max-w-sm items-start"
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
				class="lucide lucide-search text-base-content/60 absolute left-2 top-1/2 -translate-y-1/2 transform"
				><circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" /></svg
			>
		</div>
		<div class="max-h-135 flex justify-start overflow-y-auto">
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
	<Modal open={showDeleteModal} onclose={() => (showDeleteModal = false)}>
		<p>Are you sure you want to delete this draft?</p>
		<div class="mt-4 flex justify-end gap-2">
			<button class="btn btn-ghost" onclick={() => (showDeleteModal = false)}>No</button>
			<button
				class="btn btn-error"
				onclick={() => {
					confirmDelete(draftToDelete);
					showDeleteModal = false;
				}}>Yes</button
			>
		</div>
	</Modal>
{/if}
