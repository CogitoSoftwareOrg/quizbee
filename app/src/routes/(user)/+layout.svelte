<script lang="ts">
	import {
		House,
		Plus,
		Settings,
		Menu,
		PanelRightOpen,
		PanelRightClose,
		MessageCircleHeart
	} from 'lucide-svelte';
	import { page } from '$app/state';

	import Logo from '$lib/assets/icons/bee1.svg';

	import ProfileRow from '$lib/apps/users/ProfileRow.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	import SidebarNavigation from './SidebarNavigation.svelte';
	import GlobalHeader from './GlobalHeader.svelte';
	import SubscribeUser from './SubscribeUser.svelte';
	import Button from '$lib/ui/Button.svelte';
	import ThemeController from '$lib/features/ThemeController.svelte';

	const { data, children } = $props();

	const newPageColor = $derived(page.url.pathname === '/quizes/new');
	const attemptingQuiz = $derived(
		/quizes\/[0-9a-zA-Z]+\/attempts\/[0-9a-zA-Z]+/.test(page.url.pathname) &&
			!page.url.pathname.includes('/feedback')
	);
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
			<div
				class={[
					'mb-2 flex items-center',
					uiStore.globalSidebarOpen ? 'justify-between pr-2' : 'justify-center'
				]}
			>
				{#if uiStore.globalSidebarOpen}
					<a href="/home" class="relative mb-4 flex select-none items-center justify-center">
						<img src={Logo} alt="Quizbee" class="size-14 rounded-full" />
						<p class="text-primary mt-2 text-3xl font-semibold">Quizbee</p>
					</a>
				{/if}
				<button
					class={[
						'hidden w-fit cursor-pointer items-center sm:flex',
						uiStore.globalSidebarOpen ? 'mb-3' : ''
					]}
					onclick={() => uiStore.toggleGlobalSidebar()}
				>
					{#if uiStore.globalSidebarOpen}
						<PanelRightOpen class="text-neutral size-8" />
					{:else}
						<PanelRightClose class="text-neutral size-8" />
					{/if}
				</button>
			</div>

			<SidebarNavigation class="flex min-h-0 flex-1" />

			<div class="mt-auto flex flex-col items-center justify-center gap-2">
				<!-- <div class="flex items-center justify-center gap-2">
					<ThemeController />
					{#if uiStore.globalSidebarOpen}
						<MessageCircleHeart class="size-7 " />
					{/if}
				</div> -->

				<ProfileRow />
			</div>
		</aside>

		<main class="flex h-full flex-1 flex-col">
			<GlobalHeader />

			<div class={['h-full flex-1 overflow-auto sm:p-3 sm:pb-3', !attemptingQuiz && 'pb-12']}>
				{@render children?.()}
			</div>

			{#if !attemptingQuiz}
				<footer class="dock dock-sm sm:hidden">
					<a href="/home">
						<House class={page.url.pathname === '/home' ? 'text-primary' : 'text-neutral'} />
					</a>
					<div>
						<Button
							style={page.url.pathname === '/quizes/new' ? 'ghost' : 'solid'}
							color={page.url.pathname === '/quizes/new' ? 'neutral' : 'primary'}
							size="lg"
							href="/quizes/new"
							circle
						>
							<Plus size={32} />
						</Button>
					</div>
					<a href="/profile">
						<Settings class={page.url.pathname === '/profile' ? 'text-primary' : 'text-neutral'} />
					</a>
				</footer>
			{/if}
		</main>
	</div>
{:catch error}
	{JSON.stringify(error)}
{/await}
