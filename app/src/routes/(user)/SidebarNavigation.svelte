<script lang="ts">
	import { page } from '$app/state';
	import { House, ChartBar, CreditCard } from 'lucide-svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	const navItems = [
		{
			name: 'home',
			label: 'Home',
			href: '/home',
			icon: House
		},
		{
			name: 'analytics',
			label: 'Analytics',
			href: '/analytics',
			icon: ChartBar
		},
		{
			name: 'billing',
			label: 'Billing',
			href: '/billing',
			icon: CreditCard
		}
	];

	const active = $derived(page.url.pathname.split('/').at(1) || 'home');

	function linkClass(name: string) {
		const base = 'btn btn-block w-full justify-start rounded-lg btn-ghost text-nowrap';
		return active === name ? `${base} text-primary` : `${base}`;
	}

	function iconClass(name: string) {
		const base = 'btn btn-circle btn-ghost w-10 h-10';
		return active === name ? `${base} text-primary` : `${base}`;
	}
</script>

<nav class="flex min-h-0 flex-1 overflow-y-auto overflow-x-hidden">
	{#if uiStore.globalSidebarOpen}
		<ul class="menu menu-vertical w-full gap-1 px-2 pb-2">
			{#each navItems as item}
				<li class="w-full">
					<a href={item.href} class={['text-left', linkClass(item.name)]}>
						<item.icon size={20} />
						{item.label}
					</a>
				</li>
			{/each}
		</ul>
	{:else}
		<div class="flex w-full flex-col items-center gap-2 py-2">
			{#each navItems as item}
				<a href={item.href} class={iconClass(item.name)} title={item.label}>
					<item.icon size={20} />
				</a>
			{/each}
		</div>
	{/if}
</nav>
