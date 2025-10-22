<script lang="ts">
	import { Button } from '@cogisoft/ui-svelte-daisy';

	import type { QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Sender } from '$lib/apps/messages/types';
	import ExplainMore from '$lib/apps/messages/ExplainMore.svelte';

	interface Props {
		quizAttempt: QuizAttemptsResponse;
		quizItems: QuizItemsResponse[];
		order: number;
		itemDecision: Decision | null;
		chatOpen?: boolean;
		userSender: Sender;
		itemId: string;
		onPrevious: () => void;
		onNext: () => void;
	}

	let { quizAttempt, quizItems, order, itemDecision, chatOpen = $bindable(false), userSender, itemId, onPrevious, onNext }: Props =
		$props();
</script>

<div class="flex justify-between gap-4 -mb-2 px-3 pt-6 sm:px-12">
	<div class="flex-1">
		{#if itemDecision}
			<ExplainMore sender={userSender} quizAttemptId={quizAttempt.id} {itemId} bind:chatOpen />
		{/if}
	</div>
	
	<div class="flex gap-4">
		{#if order > 0}
			<Button
				color="neutral"
				style="outline"
				size="lg"
				class="dark:!text-base-content/90"
				onclick={(e) => {
					e.preventDefault();
					onPrevious();
				}}
			>
				Previous
			</Button>
		{:else}
			<Button
				
				size="lg"
				class="invisible pointer-events-none"
			>
				Previous
			</Button>
		{/if}

		{#if itemDecision}
			<Button
				color="primary"
				size="lg"
				onclick={(e) => {
					e.preventDefault();
					onNext();
				}}
			>
				Next
			</Button>
		{:else}
			<Button
				
				size="lg"
				class="invisible pointer-events-none"
			>
				Next
			</Button>
		{/if}
	</div>
</div>
