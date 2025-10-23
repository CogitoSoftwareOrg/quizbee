<script lang="ts">
	import posthog from 'posthog-js';
	import { goto } from '$app/navigation';
	import { Button } from '@cogisoft/ui-svelte-daisy';

	import { postApi } from '$lib/api/call-api';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { pb } from '$lib/pb';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';

	interface Props {
		quizTemplateId: string;
		attachedFiles: AttachedFile[];
		inputText: string;
		questionCount: number;
	}

	let { quizTemplateId, attachedFiles, inputText, questionCount }: Props = $props();

	const hasFiles = $derived(attachedFiles.length > 0);
	const hasText = $derived(inputText.trim().length > 0);
	const isSubmitDisabled = $derived(!hasFiles && !hasText);

	const subscription = $derived(subscriptionStore.subscription);
	const quizUsage = $derived(subscription?.quizItemsUsage || 0);
	const quizLimit = $derived(subscription?.quizItemsLimit || 0);
	const quizRemained = $derived(quizLimit - quizUsage);

	let isLoading = $state(false);

	async function sendQuizCreation(): Promise<boolean> {
		if (questionCount > quizRemained) {
			uiStore.setPaywallOpen(true);
			return false;
		}

		isLoading = true;

		try {
			for (const attachedFile of attachedFiles) {
				const material = await pb!.collection('materials').getOne(attachedFile.materialId);
				if (material.status !== 'used') {
					pb!.collection('materials').update(attachedFile.materialId, { status: 'used' });
				}
			}

			const { quiz_id: quizId, quiz_attempt_id: quizAttemptsId } = await postApi('quizes', {
				quiz_id: quizTemplateId
			});

			posthog.capture('quiz_creation_started', {
				quizId,
				quizAttemptsId
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

<Button
	class={[
		'h-14 w-full text-lg font-semibold shadow-lg transition-all duration-200 hover:scale-[1.02] hover:shadow-xl'
	]}
	disabled={quizRemained >= questionCount && (isSubmitDisabled || isLoading)}
	onclick={sendQuizCreation}
	style={quizRemained < questionCount ? 'soft' : 'solid'}
>
	{#if isLoading}
		<span class="loading loading-md loading-spinner mr-2"></span>
		Creating quiz...
	{:else if quizRemained < questionCount}
		You have {quizRemained} questions left
	{:else}
		Start a quiz
	{/if}
</Button>
