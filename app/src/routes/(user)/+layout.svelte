<script lang="ts">
	import { userStore } from '$lib/apps/users/user.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import ThemeController from '$lib/features/ThemeController.svelte';
	import type { UserExpand } from '$lib/pb/expands.js';

	const { data, children } = $props();

	const user = $derived(userStore.user);

	// wait for user to be loaded
	$effect(() => {
		data.userLoadPromise.then((userLoad) => {
			const materials = userLoad.expand.materials_via_user || [];
			const quizAttempts = userLoad.expand.quizAttempts_via_user || [];
			const quizes = userLoad.expand.quizes_via_author || [];

			materialsStore.materials = materials;
			quizAttemptsStore.quizAttempts = quizAttempts;
			quizesStore.quizes = quizes;

			userLoad.expand = {} as UserExpand;
			userStore.user = userLoad;
			userStore.setLoaded();
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
	<div class="flex h-screen items-center justify-center">
		<div class="loading loading-spinner loading-xl"></div>
		<p>We are loading app for you... :3</p>
	</div>
{:then}
	{@render children?.()}
{:catch error}
	{JSON.stringify(error)}
{/await}
