<script lang="ts">
	import { goto } from '$app/navigation';
	import { computeApiUrl } from '$lib/api/compute-url';
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
		attachedFiles: AttachedFile[];
		inputText: string;
		selectedDifficulty: string;
		questionCount: number;
	}

	let { attachedFiles, inputText, selectedDifficulty, questionCount }: Props = $props();

	const hasFiles = $derived(attachedFiles.length > 0);
	const hasText = $derived(inputText.trim().length > 0);
	const isSubmitDisabled = $derived(!hasFiles && !hasText);

	let isLoading = $state(false);

	async function sendQuizCreation(): Promise<boolean> {
		isLoading = true;

		try {
			const selectedMaterialIds = attachedFiles
				.filter((file) => file.materialId)
				.map((file) => file.materialId!);

			const createQuizPayload = {
				query: inputText,
				material_ids: selectedMaterialIds,
				with_attempt: true,
				number_of_questions: questionCount,
				difficulty: selectedDifficulty.toLowerCase()
			};

			const createResponse = await fetch(`${computeApiUrl()}quizes`, {
				method: 'POST',
				body: JSON.stringify(createQuizPayload),
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});

			if (!createResponse.ok) {
				const errorText = await createResponse.text();
				console.error('Failed to create quiz:', errorText);
				return false;
			}

			const { quiz_id: quizId, quiz_attempt_id: quizAttemptsId } = await createResponse.json();
			console.log('Quiz created:', quizId, 'Attempt created:', quizAttemptsId);

			const updateQuizPayload = {
				limit: 50 // for now just gurantee total number of questions
			};

			const updateResponse = await fetch(`${computeApiUrl()}quizes/${quizId}`, {
				method: 'PATCH',
				body: JSON.stringify(updateQuizPayload),
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});

			if (!updateResponse.ok) {
				const errorText = await updateResponse.text();
				console.error('Failed to update quiz settings:', errorText);
				return false;
			}

			const updateResult = await updateResponse.json();
			console.log('Quiz settings updated:', updateResult);

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
