<script lang="ts">
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { type QuizExpand } from '$lib/pb';
	import { type QuizesResponse } from '$lib/pb';
	import { generateId } from '$lib/utils/generate-id';
	import { pb } from '$lib/pb';
	import { createAttachedFileFromMaterial } from '../new/createAttachedFileFromMaterial';
	import { truncateFileName } from '$lib/utils/truncuate-file-name';
	import { generateUniqueTitle } from '$lib/utils/generate-unique-title';
	import { createDraft } from '../new/createDraft';
	import { addExistingMaterial } from '../new/addExistingMaterial';
	import { removeFile } from '../new/removeFile';

	interface Props {
		quizTemplateId: string;
		title: string;
		inputText: string;
		attachedFiles: AttachedFile[];
		selectedDifficulty: string;
		questionCount: number;
		draftSwitch: boolean;
		searchQuery: string;

		onQuizSelected?: () => void;
	}

	let {
		quizTemplateId = $bindable(),
		title = $bindable(),
		inputText = $bindable(),
		attachedFiles = $bindable(),
		selectedDifficulty = $bindable(),
		draftSwitch = $bindable(),
		questionCount = $bindable(),

		searchQuery,

		onQuizSelected = () => {}
	}: Props = $props();

	const previousQuizes = $derived(quizesStore.quizes.filter((q: any) => q.status !== 'draft'));
	const filteredQuizes = $derived(
		previousQuizes.filter(
			(q) =>
				q.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(q.query && q.query.toLowerCase().includes(searchQuery.toLowerCase()))
		)
	);

	async function handleQuizClick(quiz: any) {
		title = quiz.title;
		inputText = quiz.query;

		for (const [index, file] of attachedFiles.entries()) {
			await removeFile(index, attachedFiles, quizTemplateId);
		}
		for (const materialId of quiz.materials || []) {
			console.log('materialId', materialId);
			const attachedFile = await addExistingMaterial(materialId, quizTemplateId);
			if (attachedFile) {
				attachedFiles = [...attachedFiles, attachedFile];
			}
		}

		selectedDifficulty = quiz.selectedDifficulty;
		questionCount = quiz.itemsLimit;
		onQuizSelected();
	}
</script>

<div class="border-base-200 h-full w-full flex-shrink-0 overflow-y-auto border-r">
	<div class="space-y-3">
		{#if filteredQuizes.length === 0}
			<div class="mt-8 text-center">
				<p class="text-sm">No previous quizes yet</p>
				<p class="mt-1 text-xs">Create your first quiz!</p>
			</div>
		{:else}
			{#each filteredQuizes as quiz}
				<div
					class="} border-base-200 cursor-pointer rounded-lg border p-4 shadow-sm transition-shadow hover:bg-red-100 hover:shadow-md"
					onclick={() => handleQuizClick(quiz)}
					onkeydown={(e) => e.key === 'Enter' && handleQuizClick(quiz)}
					role="button"
					tabindex="0"
				>
					<h3 class="mb-1 truncate text-left font-medium" title={quiz.title || `Quiz ${quiz.id}`}>
						{quiz.title || `Quiz ${quiz.id}`}
					</h3>

					{#if quiz.query}
						<p class="text-primary mb-1 text-left text-xs">
							<span class="font-medium">Query:</span>
							{quiz.query.length > 160 ? quiz.query.substring(0, 160) + '...' : quiz.query}
						</p>
					{/if}
					{#if quiz.materials && quiz.materials.length > 0}
						<p class="text-success text-left text-xs">
							<span class="font-medium">Materials:</span>
							{quiz.materials.length} file(s)
						</p>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>
