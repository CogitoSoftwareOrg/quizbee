<script lang="ts">
	import MyQuizes from '$lib/apps/quizes/MyQuizes.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';

	const quizAttempts = $derived(quizAttemptsStore.quizAttempts);
	const materials = $derived(materialsStore.materials);
	const user = $derived(userStore.user);
</script>

<div class="mx-auto flex h-full max-w-6xl flex-col items-center justify-center gap-4">
	{#if user}
		<MyQuizes class=" w-full flex-1 px-5" {quizAttempts} {materials} userId={user.id} />
	{/if}
</div>
