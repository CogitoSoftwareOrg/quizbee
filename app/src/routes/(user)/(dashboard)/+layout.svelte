<script lang="ts">
	import { PanelRightOpen, PanelRightClose } from 'lucide-svelte';
	import ThemeController from '$lib/features/ThemeController.svelte';
	import ProfileRow from '$lib/apps/users/ProfileRow.svelte';
	import SidebarNavigation from './SidebarNavigation.svelte';

	const { children } = $props();

	let sidebarOpen = $state(true);
	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}
</script>

<div class="flex h-dvh w-full overflow-hidden">
	<aside
		class={[
			'bg-base-100 border-base-200 z-10 flex h-full shrink-0 flex-col border-r pt-4 transition-all duration-300 ease-in-out',
			sidebarOpen ? 'w-56' : 'w-14'
		]}
	>
		<a href="/home" class="relative mb-4 flex select-none items-center justify-center gap-2 px-2">
			<div class="bg-primary/10 size-8 rounded"></div>
			{#if sidebarOpen}
				<p class="text-primary text-xl font-semibold">Quizbee</p>
			{/if}
		</a>

		<SidebarNavigation {sidebarOpen} />

		<ProfileRow {sidebarOpen} />
	</aside>

	<main class="flex h-full flex-1 flex-col">
		<header class="border-base-200 flex items-center justify-between border-b px-3 py-3">
			<div class="flex items-center gap-2">
				<label class="swap swap-rotate">
					<input class="hidden" type="checkbox" checked={sidebarOpen} onchange={toggleSidebar} />
					<PanelRightOpen class="swap-on text-neutral-500" size={24} />
					<PanelRightClose class="swap-off text-neutral-500" size={24} />
				</label>
				<h1 class="hidden text-sm font-semibold sm:block">Welcome</h1>
			</div>

			<ThemeController />
		</header>

		<div class="h-full flex-1 overflow-auto p-2 sm:p-3">
			{@render children?.()}
		</div>
	</main>
</div>
