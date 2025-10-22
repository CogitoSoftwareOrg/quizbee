<script lang="ts">
	import MyQuizes from '$lib/apps/quizes/MyQuizes.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';

	const quizes = $derived(
		quizesStore.quizes.filter((quiz) => quiz.status !== 'draft' && quiz.status !== 'creating')
	);
	const materials = $derived(materialsStore.materials);
</script>

<div class="mx-auto flex h-full max-w-6xl flex-col items-center justify-center gap-4">
	<MyQuizes class="w-full flex-1" {quizes} {materials} />
</div>
