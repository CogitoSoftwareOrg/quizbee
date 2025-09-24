<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	import Button from '$lib/ui/Button.svelte';
	import type { QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';

	interface Props {
		quizItems: QuizItemsResponse[];
		order: number;
		itemDecision: Decision | null;
	}

	const { quizItems, order, itemDecision }: Props = $props();

	function gotoItem(idx: number) {
		const max = quizItems.length ? quizItems.length - 1 : 0;
		const clamped = Math.max(0, Math.min(idx, max));
		const u = new URL(page.url);
		u.searchParams.set('order', String(clamped));
		goto(u, { replaceState: clamped !== idx, keepFocus: true, noScroll: true });
	}

	function gotoFinal() {
		const u = new URL(page.url);
		goto(`${u.pathname}/feedback`, { replaceState: false, keepFocus: true, noScroll: true });
	}
</script>

<div class="pointer-events-none absolute -left-2 top-1/2 z-10 hidden -translate-y-1/2 md:block">
	<Button
		class="pointer-events-auto"
		color="neutral"
		style="outline"
		circle
		size="xl"
		onclick={() => {
			gotoItem(order - 1);
		}}
	>
		<ChevronLeft size={42} />
	</Button>
</div>

<div class="pointer-events-none absolute -right-2 top-1/2 z-10 hidden -translate-y-1/2 md:block">
	<Button
		class="pointer-events-auto"
		color="neutral"
		style="outline"
		circle
		size="xl"
		onclick={() => {
			if (!itemDecision) return;
			if (order + 1 === quizItems.length) {
				gotoFinal();
				return;
			}
			gotoItem(order + 1);
		}}
	>
		<ChevronRight size={42} />
	</Button>
</div>
