<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import { userStore } from '$lib/apps/users/user.svelte.js';

	const {} = $props();

	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId)
	);
	const quiz = $derived(quizesStore.quizes.find((q) => q.id === quizAttempt?.quiz));
	const quizItems = $derived(
		quiz?.expand.quizItems_via_quiz?.toSorted((a, b) => a.created.localeCompare(b.created)) || []
	);

	let itemIdx = $derived.by(() => {
		const itemIdxStr = page.url.searchParams.get('itemIdx');
		let itemIdx = itemIdxStr ? parseInt(itemIdxStr) : 0;
		const maxIdx = quizItems.length > 0 ? quizItems.length - 1 : 0;
		if (itemIdx < 0) itemIdx = 0;
		if (itemIdx > maxIdx) itemIdx = maxIdx;
		return itemIdx;
	});
	const item = $derived(quizItems[itemIdx]);

	$effect(() => {
		if (userStore.loaded && !quizAttempt) goto('/home');
	});

	function gotoItem(idx: number) {
		const max = quizItems.length ? quizItems.length - 1 : 0;
		const clamped = Math.max(0, Math.min(idx, max));
		const u = new URL(page.url);
		u.searchParams.set('itemIdx', String(clamped));
		goto(u, { replaceState: clamped !== idx, keepfocus: true, noscroll: true });
	}
</script>

{itemIdx}
{item?.question}
<div>
	{quizAttemptId}
	<button
		class="btn"
		onclick={() => {
			gotoItem(itemIdx - 1);
		}}>Previous</button
	>
	<button
		class="btn"
		onclick={() => {
			gotoItem(itemIdx + 1);
		}}>Next</button
	>
</div>
