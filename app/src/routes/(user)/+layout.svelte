<script lang="ts">
	import { userStore } from '$lib/apps/users/user.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';

	const { data, children } = $props();

	const user = $derived(userStore.user);

	// wait for user to be loaded
	$effect(() => {
		data.userLoadPromise.then((user) => {
			const materials = user.expand.materials_via_user || [];
			const quizAttempts = user.expand.quizAttempts_via_user || [];
			const quizes = user.expand.quizes_via_author || [];

			userStore.user = user;
			materialsStore.materials = materials;
			quizAttemptsStore.quizAttempts = quizAttempts;
			quizesStore.quizes = quizes;
		});
	});

	$effect(() => {
		if (!user) return;
		userStore.subscribe(user.id);
		materialsStore.subscribe(user.id);
		quizAttemptsStore.subscribe(user.id);
		quizesStore.subscribe(user.id);

		return () => {
			userStore.unsubscribe(user.id);
			materialsStore.unsubscribe();
			quizAttemptsStore.unsubscribe();
			quizesStore.unsubscribe();
		};
	});
</script>

{#await data.userLoadPromise}
	<div class="loading loading-spinner loading-lg"></div>
{:then}
	{@render children?.()}
	{JSON.stringify(user)}
{:catch error}
	{JSON.stringify(error)}
{/await}
