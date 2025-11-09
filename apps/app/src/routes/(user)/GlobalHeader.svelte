<script lang="ts">
	import { page } from '$app/state';
	import {
		PanelRightOpen,
		PanelRightClose,
		ChevronLeft,
		Menu,
		MessageCircleHeart
	} from 'lucide-svelte';
	import { Button } from '@quizbee/ui-svelte-daisy';

	import { uiStore } from '$lib/apps/users/ui.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
	import type { Decision } from '$lib/apps/quiz-attempts/types';

	const isNewQuizPage = $derived(page.url.pathname === '/quizes/new');

	const attemptingQuiz = $derived(
		/quizes\/[0-9a-zA-Z]+\/attempts\/[0-9a-zA-Z]+/.test(page.url.pathname) &&
			!page.url.pathname.includes('/feedback')
	);

	const quiz = $derived(quizesStore.quizes.find((q) => q.id === page.params.quizId));
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === page.params.quizAttemptId)
	);

	const quizDecisions = $derived((quizAttempt?.choices as Decision[]) || []);
	const quizItems = $derived(quizItemsStore.quizItemsMap.get(quiz?.id || '') || []);

	const order = $derived.by(() => {
		const orderStr = page.url.searchParams.get('order');
		let order = orderStr ? parseInt(orderStr) : 0;
		const maxIdx = quizItems.length - 1;
		if (order < 0) order = 0;
		if (order > maxIdx) order = maxIdx;
		return order;
	});
	const currentItem = $derived(quizItems.find((qi) => qi.order === order));
	const itemToAnswer = $derived(quizItems.find((qi) => !quizDecisions.at(qi.order)));

	function getTitle() {
		const t = page.url.pathname.split('/').at(1);
		return `${t?.charAt(0).toUpperCase()}${t?.slice(1)}`;
	}
</script>

<header
	class={[
		'flex items-center justify-between px-2 py-2',
		//!isNewQuizPage &&
		'border-base-200 border-b'
	]}
>
	<div class="flex items-center gap-3">
		<!-- Mobile Sidebar Toggle -->
		<button class="flex w-fit items-center sm:hidden" onclick={() => uiStore.toggleGlobalSidebar()}>
			<Menu class="size-6 text-neutral-500" />
		</button>
		{#if !attemptingQuiz}
			<!-- <h1 class="hidden font-semibold sm:block">{getTitle()}</h1> -->
		{:else if attemptingQuiz}
			{#if quizAttempt?.feedback}
				<Button
					class="underline"
					color="neutral"
					style="ghost"
					href={`/quizes/${quiz?.id}/attempts/${quizAttempt?.id}/feedback`}
				>
					<ChevronLeft /> Feedback
				</Button>
			{/if}

			{#if quiz?.title}
				<div class="hidden text-sm font-semibold">{quiz.title}</div>
			{/if}
		{/if}
	</div>

	<!-- Always -->
	<div class="flex items-center gap-1"></div>
</header>
