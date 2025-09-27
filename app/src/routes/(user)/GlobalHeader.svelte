<script lang="ts">
	import { page } from '$app/state';
	import { PanelRightOpen, PanelRightClose, ChevronLeft } from 'lucide-svelte';

	import { uiStore } from '$lib/apps/users/ui.svelte';
	import ThemeController from '$lib/features/ThemeController.svelte';
	import Button from '$lib/ui/Button.svelte';

	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
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
	const quizItems = $derived(
		quiz?.expand.quizItems_via_quiz?.toSorted((a, b) => a.order - b.order) || []
	);

	const order = $derived.by(() => {
		const orderStr = page.url.searchParams.get('order');
		let order = orderStr ? parseInt(orderStr) : 0;
		const maxIdx = quizItems.length - 1;
		if (order < 0) order = 0;
		if (order > maxIdx) order = maxIdx;
		return order;
	});
	const currentItem = $derived(quizItems.find((qi) => qi.order === order));
	const itemToAnswer = $derived(
		quizItems.find((qi) => !quizDecisions.some((d) => d.itemId === qi.id))
	);

	function getTitle() {
		const t = page.url.pathname.split('/').at(1);
		return `${t?.charAt(0).toUpperCase()}${t?.slice(1)}`;
	}
</script>

<header
	class={[
		'flex items-center justify-between px-3 py-3',
		!isNewQuizPage && 'border-base-200 border-b'
	]}
>
	<div class="flex items-center gap-2">
		<label class="swap swap-rotate">
			<input
				class="hidden"
				type="checkbox"
				checked={uiStore.globalSidebarOpen}
				onchange={() => {
					uiStore.toggleGlobalSidebar();
				}}
			/>
			<PanelRightOpen class="swap-on text-neutral-500" size={24} />
			<PanelRightClose class="swap-off text-neutral-500" size={24} />
		</label>
		{#if !attemptingQuiz}
			<h1 class="hidden font-semibold sm:block">{getTitle()}</h1>
		{:else if attemptingQuiz}
			{#if quizAttempt?.feedback}
				<Button
					color="neutral"
					style="ghost"
					href={`/quizes/${quiz?.id}/attempts/${quizAttempt?.id}/feedback`}
				>
					<ChevronLeft /> Feedback
				</Button>
			{/if}

			{#if quiz?.title}
				<div class="text-sm font-semibold">{quiz.title}</div>
			{/if}

			<ul class="flex flex-1 flex-wrap items-center gap-2">
				{#each quizItems as quizItem, index}
					{@const decision = quizDecisions.find((d) => d.itemId === quizItem.id)}

					<li>
						<Button
							disabled={!decision && quizItem.order > (itemToAnswer?.order || 0)}
							color={decision?.correct
								? 'success'
								: decision && !decision?.correct
									? 'error'
									: 'neutral'}
							href={`/quizes/${quiz?.id}/attempts/${quizAttempt?.id}?order=${quizItem.order}`}
							style={currentItem?.id === quizItem.id ? 'solid' : 'outline'}
							size="sm"
							circle
						>
							{index + 1}
						</Button>
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	<!-- Always -->
	<ThemeController />
</header>
