<script lang="ts">
	import { House, Plus, Settings } from 'lucide-svelte';

	import Logo from '$lib/assets/icons/bee1.svg';

	import ProfileRow from '$lib/apps/users/ProfileRow.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	import SidebarNavigation from './SidebarNavigation.svelte';
	import GlobalHeader from './GlobalHeader.svelte';
	import SubscribeUser from './SubscribeUser.svelte';
	import Button from '$lib/ui/Button.svelte';

	const { data, children } = $props();
</script>

<SubscribeUser />

{#await data.userLoadPromise}
	<div class="flex h-screen items-center justify-center">
		<div class="loading loading-spinner loading-xl"></div>
		<p>We are loading app for you... :3</p>
	</div>
{:then}
	<div class="flex h-dvh w-full overflow-hidden">
		<aside
			class={[
				'bg-base-100 border-base-200 z-10 h-full shrink-0 flex-col border-r pt-2 transition-all duration-300 ease-in-out',
				uiStore.globalSidebarOpen ? 'w-56' : 'w-14',
				'hidden sm:flex'
			]}
		>
			<a href="/home" class="relative mb-4 flex select-none items-center justify-center gap-1">
				<img src={Logo} alt="Quizbee" class="bg-primary/10 size-12 rounded-full" />
				{#if uiStore.globalSidebarOpen}
					<p class="text-primary text-3xl font-semibold">Quizbee</p>
				{/if}
			</a>

			<SidebarNavigation class="flex min-h-0 flex-1" />

			<ProfileRow />
		</aside>

		<main class="flex h-full flex-1 flex-col">
			<GlobalHeader />

			<div class="h-full flex-1 overflow-auto pb-12 sm:p-3 sm:pb-3">
				{@render children?.()}
			</div>

			<footer class="dock dock-sm sm:hidden">
				<a href="/home">
					<House />
				</a>
				<div>
					<Button size="lg" href="/quizes/new" circle>
						<Plus size={32} />
					</Button>
				</div>
				<a href="/profile">
					<Settings />
				</a>
			</footer>
		</main>
	</div>
{:catch error}
	{JSON.stringify(error)}
{/await}
