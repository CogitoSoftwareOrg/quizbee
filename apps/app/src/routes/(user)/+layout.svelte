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
	import Splash from './Splash.svelte';
	import { onMount } from 'svelte';
	import { pb } from '$lib/pb';

	const { data, children } = $props();

	const mobile = new MediaQuery('(max-width: 640px)');

	const newPageColor = $derived(page.url.pathname === '/quizes/new');
	const attemptingQuiz = $derived(
		/quizes\/[0-9a-zA-Z]+\/attempts\/[0-9a-zA-Z]+/.test(page.url.pathname) &&
			!page.url.pathname.includes('/feedback')
	);

	// Sidebar swipe gesture tracking
	let rootElement = $state<HTMLDivElement | null>(null);
	let sidebarSwipeStartX = $state(0);
	let sidebarSwipeStartY = $state(0);

	const SIDEBAR_SWIPE_THRESHOLD = 70; // Minimum swipe distance to trigger
	const SIDEBAR_EDGE_THRESHOLD = 50; // Area from left edge to detect swipe start

	function handleSidebarSwipeStart(e: TouchEvent) {
		// Only on mobile, not during quiz, and if sidebar not already open
		if (!mobile.current || attemptingQuiz || uiStore.globalSidebarOpen) return;

		sidebarSwipeStartX = e.touches[0].clientX;
		sidebarSwipeStartY = e.touches[0].clientY;
	}

	function handleSidebarSwipeEnd(e: TouchEvent) {
		// Guard: only process if conditions are met
		if (!mobile.current || attemptingQuiz || uiStore.globalSidebarOpen || !sidebarSwipeStartX)
			return;

		// Guard: must start from left edge
		if (sidebarSwipeStartX >= SIDEBAR_EDGE_THRESHOLD) {
			sidebarSwipeStartX = 0;
			sidebarSwipeStartY = 0;
			return;
		}

		const diffX = e.changedTouches[0].clientX - sidebarSwipeStartX;
		const diffY = Math.abs(e.changedTouches[0].clientY - sidebarSwipeStartY);

		// Check if it's a horizontal rightward swipe (not vertical scroll)
		if (diffX > SIDEBAR_SWIPE_THRESHOLD && diffX > diffY) {
			uiStore.setGlobalSidebarOpen(true);
			// Haptic feedback for better UX
			if ('vibrate' in navigator) navigator.vibrate(10);
		}

		// Reset
		sidebarSwipeStartX = 0;
		sidebarSwipeStartY = 0;
	}

	// Enable View Transitions API for smooth page transitions
	// Optimized for mobile responsiveness - resolve immediately to prevent click delay
	onNavigate((navigation) => {
		if (!document.startViewTransition) return;

		return new Promise((resolve) => {
			// Resolve BEFORE starting transition to avoid blocking navigation
			resolve();

			document.startViewTransition(async () => {
				document.documentElement.setAttribute('data-vt', mobile.current ? 'slide' : 'parallax');
				await navigation.complete;
			});
		});
	});

	onMount(() => {
		if (!pb?.authStore.isValid) {
			sessionStorage.setItem('postLoginPath', page.url.pathname + page.url.search);
			goto('/sign-in', { replaceState: true });
		} else if (pb?.authStore.isValid && !pb.authStore.record?.verified) {
			goto('/verify-email', { replaceState: true });
		}
	});
</script>

<SubscribeUser />

{#await data.userLoadPromise}
	<Splash />
{:then}
	<div
		bind:this={rootElement}
		class="flex h-dvh w-full overflow-hidden"
		ontouchstart={handleSidebarSwipeStart}
		ontouchend={handleSidebarSwipeEnd}
	>
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

		<main
			class={['flex h-full min-w-0 flex-1 flex-col sm:pt-4', !attemptingQuiz && 'pb-12 sm:pb-0']}
		>
			<header class="mobile-header sm:hidden">
				<GlobalHeader />
			</header>

			<div class={['h-full min-w-0 flex-1 overflow-auto', !attemptingQuiz && '']}>
				<div id="page-root" class={['h-full min-h-full', !attemptingQuiz && 'p-4 sm:p-3']}>
					{@render children?.()}
				</div>
			</div>

			{#if !attemptingQuiz}
				<footer class="mobile-dock-footer dock dock-sm z-50 sm:hidden">
					<a href="/home" data-sveltekit-preload-data="tap" class="dock-item">
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
					<a href="/profile" data-sveltekit-preload-data="tap" class="dock-item">
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
	fullHeight
	backdrop
	open={uiStore.globalSidebarOpen && mobile.current}
	onclose={() => {
		if (mobile.current) {
			uiStore.setGlobalSidebarOpen(false);
		}
	}}
	placement="left"
	noPadding
	class="min-w-[66vw]"
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
		/* Критично для производительности на мобильных */
		touch-action: manipulation;
		-webkit-tap-highlight-color: transparent;
	}

	/* Добавляем активное состояние для тактильной обратной связи */
	.mobile-dock-footer .dock-item {
		touch-action: manipulation;
		-webkit-tap-highlight-color: transparent;
		transition:
			transform 0.1s ease-out,
			opacity 0.1s ease-out;
	}

	.mobile-dock-footer .dock-item:active {
		transform: scale(0.92);
		opacity: 0.7;
	}

	.mobile-header {
		view-transition-name: mobile-header;
	}

	.desktop-sidebar {
		view-transition-name: desktop-sidebar;
	}
</style>
