<script lang="ts">
	import { MediaQuery } from 'svelte/reactivity';
	import { PanelRightOpen, PanelRightClose } from 'lucide-svelte';

	import Logo from '$lib/assets/icons/bee_v3.svg';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import ProfileRow from '$lib/apps/users/ProfileRow.svelte';
	import Feedback from '$lib/apps/users/Feedback.svelte';
	import ThemeController from '$lib/features/ThemeController.svelte';

	import SidebarNavigation from './SidebarNavigation.svelte';

	const mobile = new MediaQuery('(max-width: 640px)');

	const isExpanded = $derived(mobile.current ? true : uiStore.globalSidebarOpen);
</script>

<div class="flex h-screen flex-col pt-2">
	<div class={['flex items-center', isExpanded ? 'justify-between pr-2' : 'justify-center']}>
		{#if isExpanded}
			<a href="/home" class="relative mb-4 flex select-none items-center justify-center">
				<span class="absolute -right-7 top-2">
					<span class="badge badge-outline mb-1 mr-1 badge-xs badge-info">BETA</span>
				</span>
				<img
					src={Logo}
					alt="Quizbee"
					class="size-14 rounded-full  scale-[0.7] ml-1"
				/>
				<p class="text-primary mt-2 text-3xl font-semibold">Quizbee</p>
			</a>
		{/if}

		{#if !mobile.current}
			{#if uiStore.globalSidebarOpen}
				<button
					class={['hidden w-fit cursor-pointer items-center sm:flex', 'mb-3']}
					onclick={() => uiStore.setGlobalSidebarOpen(false)}
				>
					<PanelRightOpen class="text-neutral size-7" />
				</button>
			{:else}
				<button
					class={['hidden w-fit cursor-pointer items-center sm:flex']}
					onclick={() => uiStore.setGlobalSidebarOpen(true)}
				>
					<PanelRightClose class="text-neutral size-7" />
				</button>
			{/if}
		{/if}
	</div>

	<SidebarNavigation class="flex min-h-0 flex-1" expanded={isExpanded} />

	<div class="mt-auto flex flex-col items-center justify-center gap-2 px-2">
		<Feedback expanded={isExpanded} />
		<ThemeController expanded={isExpanded} />

		<ProfileRow class="w-full" expanded={isExpanded} />
	</div>
</div>
