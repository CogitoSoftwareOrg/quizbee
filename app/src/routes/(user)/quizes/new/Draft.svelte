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
	import { FilePlus } from 'lucide-svelte';

	interface Props {
		quizTemplateId: string;
		title: string;
		inputText: string;
		attachedFiles: AttachedFile[];
		selectedDifficulty: string;
		questionCount: number;
		previousQuizes: any[];
		avoidRepeat: boolean;
	}
	

	let {
		title = $bindable(),
		quizTemplateId = $bindable(),
		inputText = $bindable(),
		attachedFiles = $bindable(),
		selectedDifficulty = $bindable(),
		questionCount = $bindable(),
		previousQuizes = $bindable(),
		avoidRepeat = $bindable()
	}: Props = $props();

	const drafts = $derived(quizesStore.quizes.filter((q: any) => q.status === 'draft'));

	// states
	let showModal = $state(false);
	let searchQuery = $state('');
	let draftSwitch = $state(true);
	let showDeleteModal = $state(false);
	let draftToDelete: any = $state(null);

	// EFFECTS

	// Debounced update for all fields
	let updateTimeout: ReturnType<typeof setTimeout> | undefined;
	let pendingUpdates: Record<string, any> = {};

	function scheduleUpdate(updates: Record<string, any>) {
		if (!quizTemplateId || draftSwitch) return;

		// Merge new updates with pending ones
		pendingUpdates = { ...pendingUpdates, ...updates };

		// Clear existing timeout
		if (updateTimeout) {
			clearTimeout(updateTimeout);
		}

		// Schedule batch update
		updateTimeout = setTimeout(() => {
			if (Object.keys(pendingUpdates).length > 0) {
				pb!.collection('quizes').update(quizTemplateId, pendingUpdates);
				pendingUpdates = {};
			}
		}, 400);
	}

	// Title pb update
	$effect(() => {
		const _ = title;
		untrack(() => {
			scheduleUpdate({ title: title });
		});
	});

	// Difficulty pb update
	$effect(() => {
		const _ = selectedDifficulty;
		untrack(() => {
			scheduleUpdate({ difficulty: selectedDifficulty });
		});
	});

	// Question count pb update
	$effect(() => {
		const _ = questionCount;
		untrack(() => {
			scheduleUpdate({ itemsLimit: questionCount });
		});
	});

	// Input text pb update
	$effect(() => {
		const _ = inputText;
		untrack(() => {
			if (inputText) {
				scheduleUpdate({ query: inputText });
			}
		});
	});


	$effect(() => {
		const _ = avoidRepeat;
		untrack(() => {
			scheduleUpdate({ avoidRepeat: avoidRepeat });
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
</script>

{#if previousQuizes.length > 0}
	<div class="mt-2 flex justify-center">
		<button
			class="btn btn-xs btn-outline flex items-center text-sm"
			onclick={() => (showModal = true)}
		>
			<FilePlus class="mb-0.5 h-4 w-4" />
			<span class=" ">Use previous quiz settings</span>
		</button>
	</div>
{/if}

{#if showModal}
	<Modal
		open={showModal}
		onclose={() => (showModal = false)}
		class="max-h-screen max-w-sm items-start"
	>
		<h3 class="text-center text-2xl font-bold">Choose a quiz to copy configuration from</h3>
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
				bind:draftSwitch
				bind:questionCount
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
