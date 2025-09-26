<script lang="ts">
	import AttemptsHistory from '$lib/apps/quiz-attempts/AttemptsHistory.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';

	const quizAttempts = $derived(quizAttemptsStore.quizAttempts);
	const quizes = $derived(quizesStore.quizes);
	const materials = $derived(materialsStore.materials);
</script>

<div class="mx-auto flex h-full max-w-6xl flex-col items-center justify-center gap-4">
	<AttemptsHistory class="w-full flex-1" {quizAttempts} {quizes} {materials} />
</div>
