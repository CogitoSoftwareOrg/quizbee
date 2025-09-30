<script lang="ts">
	import { goto } from '$app/navigation';
	import { postApi } from '$lib/api/call-api';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	type AttachedFile = {
		file?: File;
		previewUrl: string | null;
		materialId?: string;
		material?: import('$lib/pb/pocketbase-types').MaterialsResponse;
		name: string;
		uploadPromise?: Promise<import('$lib/pb/pocketbase-types').MaterialsResponse>;
		isUploading?: boolean;
		uploadError?: string;
	};

	interface Props {
		quizTemplateId: string;
		attachedFiles: AttachedFile[];
		inputText: string;
		selectedDifficulty: string;
		questionCount: number;
	}

	let { quizTemplateId, attachedFiles, inputText, selectedDifficulty, questionCount }: Props =
		$props();

	const hasFiles = $derived(attachedFiles.length > 0);
	const hasText = $derived(inputText.trim().length > 0);
	const isSubmitDisabled = $derived(!hasFiles && !hasText);

	let isLoading = $state(false);

	async function sendQuizCreation(): Promise<boolean> {
		isLoading = true;

		try {
			const selectedMaterialIds = attachedFiles.map((file) => file.materialId!);

			const { quiz_id: quizId, quiz_attempt_id: quizAttemptsId } = await postApi('quizes', {
				quiz_id: quizTemplateId,
				with_attempt: true
				// query: inputText,
				// material_ids: selectedMaterialIds,
				// number_of_questions: questionCount,
				// difficulty: selectedDifficulty.toLowerCase()
			});

			console.log('Quiz created:', quizId, 'Attempt created:', quizAttemptsId);

			uiStore.setGlobalSidebarOpen(false);
			await goto(`/quizes/${quizId}/attempts/${quizAttemptsId}`);

			return true;
		} catch (error) {
			console.error('An unexpected error occurred during quiz creation:', error);
			return false;
		} finally {
			isLoading = false;
		}
	}
</script>

<button
	class="btn btn-primary transform rounded-2xl px-16 py-8 text-3xl font-bold shadow-lg transition-all duration-200 hover:scale-105 hover:shadow-xl"
	disabled={isSubmitDisabled || isLoading}
	onclick={sendQuizCreation}
>
	{#if isLoading}
		<span class="loading loading-spinner loading-md mr-2"></span>
		Creating quiz...
	{:else}
		Start a quiz
	{/if}
</button>
