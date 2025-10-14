<script lang="ts">
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	import { Button } from '@cogisoft/ui-svelte-daisy';

	import type { QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';

	interface Props {
		quizAttempt: QuizAttemptsResponse;
		quizItems: QuizItemsResponse[];
		order: number;
		itemDecision: Decision | null;
		chatOpen: boolean;
		onPrevious: () => void;
		onNext: () => void;
	}

	const { quizAttempt, quizItems, order, itemDecision, chatOpen, onPrevious, onNext }: Props =
		$props();

	const leftClass = $derived(chatOpen ? 'left-2' : 'left-8 lg:left-16 xl:left-24');
	const rightClass = $derived(chatOpen ? 'right-2' : 'right-8 lg:right-16 xl:right-24');
</script>

{#if order > 0}
	<div
		class="pointer-events-none absolute {leftClass} top-1/2 z-10 hidden -translate-y-1/2 transition-all duration-300 md:block"
	>
		<Button
			class="pointer-events-auto"
			color="neutral"
			style="ghost"
			circle
			size="lg"
			onclick={onPrevious}
		>
			<ChevronLeft size={40} />
		</Button>
	</div>
{/if}

{#if itemDecision}
	<div
		class="pointer-events-none absolute {rightClass} top-1/2 z-10 hidden -translate-y-1/2 transition-all duration-300 md:block"
	>
		<Button
			class="pointer-events-auto"
			color="neutral"
			style="ghost"
			circle
			size="lg"
			onclick={onNext}
		>
			<ChevronRight size={40} />
		</Button>
	</div>
{/if}
