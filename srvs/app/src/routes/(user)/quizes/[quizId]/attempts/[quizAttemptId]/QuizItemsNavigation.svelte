<script lang="ts">
	import { Button } from '@quizbee/ui-svelte-daisy';

	import type { QuizAttemptsResponse, QuizItemsResponse, QuizesResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import type { Sender } from '$lib/apps/messages/types';
	import ExplainMore from '$lib/apps/messages/ExplainMore.svelte';

	interface Props {
		quizAttempt: QuizAttemptsResponse;
		quiz: QuizesResponse;
		quizItems: QuizItemsResponse[];
		order: number;
		itemDecision: Decision | null;
		chatOpen?: boolean;
		userSender: Sender;
		itemId: string;
		onPrevious: () => void;
		onNext: () => void;
	}

	let {
		quizAttempt,
		quiz,
		quizItems,
		order,
		itemDecision,
		chatOpen = $bindable(false),
		userSender,
		itemId,
		onPrevious,
		onNext
	}: Props = $props();
</script>

<!-- Desktop: Explain on left, Previous and Next on right -->
<div class="-mb-2 hidden justify-between gap-4 px-3 pt-6 sm:px-12 md:flex">
	<div class="flex-1">
		{#if itemDecision}
			<ExplainMore
				{quiz}
				sender={userSender}
				quizAttemptId={quizAttempt.id}
				{itemId}
				bind:chatOpen
			/>
		{/if}
	</div>

	<div class="flex gap-4">
		{#if order > 0}
			<Button
				color="neutral"
				style="outline"
				size="lg"
				class="dark:text-base-content/90"
				onclick={(e) => {
					e.preventDefault();
					onPrevious();
				}}
			>
				Previous
			</Button>
		{:else}
			<Button size="lg" class="pointer-events-none invisible">Previous</Button>
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
			<Button size="lg" class="pointer-events-none invisible">Next</Button>
		{/if}
	</div>
</div>

<!-- Mobile: Previous on left, Explain and Next stacked on right -->
<div class="-mb-2 flex flex-col gap-2 px-1 pt-2 md:hidden">
	<!-- Explain button - full width on top -->
	<div class="flex flex-1">
		{#if itemDecision}
			<ExplainMore
				{quiz}
				sender={userSender}
				quizAttemptId={quizAttempt.id}
				{itemId}
				bind:chatOpen
				class="flex-1"
			/>
		{/if}
	</div>

	<!-- Previous and Next buttons - side by side below Explain -->
	<div class="flex gap-2">
		<!-- Previous button -->
		{#if order > 0}
			<Button
				color="neutral"
				style="outline"
				size="lg"
				class="flex-1 dark:text-base-content/90"
				onclick={(e) => {
					e.preventDefault();
					onPrevious();
				}}
			>
				Previous
			</Button>
		{:else}
			<Button size="lg" class="pointer-events-none invisible flex-1">Previous</Button>
		{/if}

		<!-- Next button -->
		{#if itemDecision}
			<Button
				color="primary"
				size="lg"
				class="flex-1"
				onclick={(e) => {
					e.preventDefault();
					onNext();
				}}
			>
				Next
			</Button>
		{:else}
			<Button size="lg" class="pointer-events-none invisible flex-1">Next</Button>
		{/if}
	</div>
</div>
