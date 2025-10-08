<script lang="ts">
	import { goto } from '$app/navigation';
	import { postApi } from '$lib/api/call-api';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';

	interface Props {
		quizTemplateId: string;
		attachedFiles: AttachedFile[];
		inputText: string;
	}

	let { quizTemplateId, attachedFiles, inputText }: Props = $props();

	const hasFiles = $derived(attachedFiles.length > 0);
	const hasText = $derived(inputText.trim().length > 0);
	const isSubmitDisabled = $derived(!hasFiles && !hasText);

	let isLoading = $state(false);

	async function sendQuizCreation(): Promise<boolean> {
		isLoading = true;

		try {
			for (const attachedFile of attachedFiles) {
				const material = await pb!.collection('materials').getOne(attachedFile.materialId);
				if (material.status !== 'used') {
					pb!.collection('materials').update(attachedFile.materialId, { status: 'used' });
				}
			}

			const { quiz_id: quizId, quiz_attempt_id: quizAttemptsId } = await postApi('quizes', {
				quiz_id: quizTemplateId,
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
	class="btn btn-primary w-full h-14 text-lg font-semibold shadow-lg transition-all duration-200 hover:scale-[1.02] hover:shadow-xl"
	disabled={isSubmitDisabled || isLoading}
	onclick={sendQuizCreation}
>
	{#if isLoading}
		<span class="loading loading-md loading-spinner mr-2"></span>
		Creating quiz...
	{:else}
		Start a quiz
	{/if}
</button>
