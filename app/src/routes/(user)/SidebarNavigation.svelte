<script lang="ts">
	import { page } from '$app/state';
	import { House, ChartBar, CreditCard, Plus, History } from 'lucide-svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import type { ClassValue } from 'svelte/elements';
	import Button from '$lib/ui/Button.svelte';

	interface Props {
		class?: ClassValue;
	}

	const { class: className }: Props = $props();

	const navItems = [
		{
			name: '/home',
			label: 'Home',
			href: '/home',
			icon: House
		},
		{
			name: '/quizes',
			label: 'History',
			href: '/quizes',
			icon: History
		}
		// {
		// 	name: '/analytics',
		// 	label: 'Analytics',
		// 	href: '/analytics',
		// 	icon: ChartBar
		// }
	];

	const attemptingQuiz = $derived(
		/quizes\/[0-9a-zA-Z]+\/attempts\/[0-9a-zA-Z]+/.test(page.url.pathname) &&
			!page.url.pathname.includes('/feedback')
	);

	const active = $derived(page.url.pathname);

	function linkClass(name: string) {
		const base = 'btn btn-block w-full justify-start rounded-lg btn-ghost text-nowrap';
		return active === name ? `${base} text-primary` : `${base}`;
	}

	function iconClass(name: string) {
		const base = 'btn btn-circle btn-ghost w-10 h-10';
		return active === name ? `${base} text-primary` : `${base}`;
	}
</script>

<nav class={['overflow-y-auto overflow-x-hidden', className]}>
	{#if !attemptingQuiz}
		{#if uiStore.globalSidebarOpen}
			<ul class="menu menu-vertical w-full gap-1 px-2 pb-2">
				<div class="flex w-full flex-col items-center gap-2 py-2">
					<Button block size="sm" style="solid" href="/quizes/new">
						<Plus size={20} /> New Quiz
					</Button>
				</div>

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
				<div class="flex w-full flex-col items-center gap-2 py-2">
					<Button circle href="/quizes/new">
						<Plus size={20} />
					</Button>
				</div>

				{#each navItems as item}
					<a href={item.href} class={iconClass(item.name)} title={item.label}>
						<item.icon size={20} />
					</a>
				{/each}
			</div>
		{/if}
	{/if}
</nav>
