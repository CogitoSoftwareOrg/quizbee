<script lang="ts">
    import Honey from '$lib/assets/icons/honey.svg';

    import ProfileRow from '$lib/apps/users/ProfileRow.svelte';
    import { uiStore } from '$lib/apps/users/ui.svelte';

    import SidebarNavigation from './SidebarNavigation.svelte';
    import GlobalHeader from './GlobalHeader.svelte';
		import SubscribeUser from './SubscribeUser.svelte';

    const { data, children } = $props();
</script>

<SubscribeUser userLoadPromise={data.userLoadPromise} />

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