<script lang="ts">
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	import Button from '$lib/ui/Button.svelte';
	import type { QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';

	interface Props {
		quizAttempt: QuizAttemptsResponse;
		quizItems: QuizItemsResponse[];
		order: number;
		itemDecision: Decision | null;
		onPrevious: () => void;
		onNext: () => void;
	}

	const { quizAttempt, quizItems, order, itemDecision, onPrevious, onNext }: Props = $props();
</script>

{#if order > 0}
	<div class="pointer-events-none absolute -left-10 top-1/2 z-10 hidden -translate-y-1/2 md:block">
		<Button
			class="pointer-events-auto"
			color="neutral"
			style="ghost"
			circle
			size="xl"
			onclick={onPrevious}
		>
			<ChevronLeft size={52} />
		</Button>
	</div>
{/if}

{#if itemDecision}
	<div class="pointer-events-none absolute -right-10 top-1/2 z-10 hidden -translate-y-1/2 md:block">
		<Button
			class="pointer-events-auto"
			color="neutral"
			style="ghost"
			circle
			size="xl"
			onclick={onNext}
		>
			<ChevronRight size={52} />
		</Button>
	</div>
{/if}
