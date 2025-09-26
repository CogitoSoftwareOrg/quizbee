<script lang="ts">
	import { page } from '$app/state';

	import { userStore } from '$lib/apps/users/user.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';
	import type { UserExpand } from '$lib/pb/expands.js';
	import Honey from '$lib/assets/icons/honey.svg';

	import ProfileRow from '$lib/apps/users/ProfileRow.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	import SidebarNavigation from './SidebarNavigation.svelte';
	import GlobalHeader from './GlobalHeader.svelte';

	const { data, children } = $props();

	const user = $derived(userStore.user);

	// wait for user to be loaded
	$effect(() => {
		data.userLoadPromise.then(async (userLoad) => {
			const materials = userLoad?.expand.materials_via_user || [];
			const quizAttempts = userLoad?.expand.quizAttempts_via_user || [];
			const quizes = userLoad?.expand.quizes_via_author || [];

			materialsStore.materials = materials;
			quizAttemptsStore.quizAttempts = quizAttempts;
			quizesStore.quizes = quizes;

			userLoad!.expand = {} as UserExpand;
			userStore.user = userLoad!;

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
	<div class="flex h-dvh w-full overflow-hidden">
		<aside
			class={[
				'bg-base-100 border-base-200 z-10 flex h-full shrink-0 flex-col border-r pt-4 transition-all duration-300 ease-in-out',
				uiStore.globalSidebarOpen ? 'w-56' : 'w-14'
			]}
		>
			<a href="/home" class="relative mb-4 flex select-none items-center justify-center gap-2 px-2">
				<img src={Honey} alt="Quizbee" class="bg-primary/20 size-8 rounded" />
				{#if uiStore.globalSidebarOpen}
					<p class="text-primary text-xl font-semibold">Quizbee</p>
				{/if}
			</a>

			<SidebarNavigation class="flex min-h-0 flex-1" />

			<ProfileRow />
		</aside>

		<main class="flex h-full flex-1 flex-col">
			<GlobalHeader />

			<div class="h-full flex-1 overflow-auto sm:p-3">
				{@render children?.()}
			</div>
		</main>
	</div>
{:catch error}
	{JSON.stringify(error)}
{/await}
