<script lang="ts">
	import { MediaQuery } from 'svelte/reactivity';
	import { House, Plus, Settings } from 'lucide-svelte';
	import { goto, onNavigate } from '$app/navigation';
	import { page } from '$app/state';

	import { Button, Modal } from '@cogisoft/ui-svelte-daisy';

	import { uiStore } from '$lib/apps/users/ui.svelte';
	import Paywall from '$lib/apps/billing/Paywall.svelte';
	import FeedbackForm from '$lib/apps/users/FeedbackForm.svelte';

	import SidebarContent from './SidebarContent.svelte';
	import GlobalHeader from './GlobalHeader.svelte';
	import SubscribeUser from './SubscribeUser.svelte';
	import { onMount } from 'svelte';
	import { pb } from '$lib/pb';

	const { data, children } = $props();

	const mobile = new MediaQuery('(max-width: 640px)');

	const newPageColor = $derived(page.url.pathname === '/quizes/new');
	const attemptingQuiz = $derived(
		/quizes\/[0-9a-zA-Z]+\/attempts\/[0-9a-zA-Z]+/.test(page.url.pathname) &&
			!page.url.pathname.includes('/feedback')
	);

	// Enable View Transitions API for smooth page transitions
	onNavigate((navigation) => {
		if (!document.startViewTransition) return;

		return new Promise((resolve) => {
			document.startViewTransition(async () => {
				document.documentElement.setAttribute('data-vt', mobile.current ? 'slide' : 'parallax');

				resolve();
				await navigation.complete;
			});
		});
	});

	onMount(() => {
		if (!pb?.authStore.isValid) {
			sessionStorage.setItem('postLoginPath', page.url.pathname + page.url.search);
			goto('/sign-in', { replaceState: true });
		}
	});
</script>

<SubscribeUser />

{#await data.userLoadPromise}
	<div class="flex h-screen items-center justify-center">
		<div class="loading loading-spinner loading-xl"></div>
		<p>We are loading app for you... :3</p>
	</div>
{:then}
	<div class="flex h-dvh w-full overflow-hidden">
		<!-- Desktop Sidebar -->
		<aside
			class={[
				'desktop-sidebar bg-base-100 border-base-200 z-10 h-full shrink-0 flex-col border-r transition-all duration-300 ease-in-out',
				uiStore.globalSidebarOpen ? 'w-56' : 'w-14',
				'hidden sm:flex'
			]}
		>
			<SidebarContent />
		</aside>

		<main class={['flex h-full min-w-0 flex-1 flex-col sm:pt-4', 'pb-12 sm:pb-0']}>
			<header class="mobile-header sm:hidden">
				<GlobalHeader />
			</header>

			<div class={['h-full min-w-0 flex-1 overflow-auto', !attemptingQuiz && 'pb-16 sm:pb-3']}>
				<div id="page-root" class={['h-full min-h-full', !attemptingQuiz && 'p-4 sm:p-3']}>
					{@render children?.()}
				</div>
			</div>

			{#if !attemptingQuiz}
				<footer class="mobile-dock-footer dock dock-sm z-50 sm:hidden">
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

<!-- Mobile Sidebar Modal -->
<Modal
	class="h-full"
	backdrop
	open={uiStore.globalSidebarOpen && mobile.current}
	onclose={() => {
		if (mobile.current) {
			uiStore.setGlobalSidebarOpen(false);
		}
	}}
	placement="left"
	noPadding
>
	<SidebarContent />
</Modal>

<Modal
	class="max-h-[95vh] max-w-[90vw]"
	backdrop
	open={uiStore.paywallOpen}
	onclose={() => uiStore.setPaywallOpen(false)}
>
	<Paywall />
</Modal>

<Modal
	class="max-w-2xl"
	backdrop
	open={uiStore.feedbackModalOpen}
	onclose={() => uiStore.setFeedbackModalOpen(false)}
>
	<FeedbackForm />
</Modal>

<style>
	/* Исключить footer, header и sidebar из анимации */
	.mobile-dock-footer {
		view-transition-name: mobile-dock;
	}

	.mobile-header {
		view-transition-name: mobile-header;
	}

	.desktop-sidebar {
		view-transition-name: desktop-sidebar;
	}
</style>
