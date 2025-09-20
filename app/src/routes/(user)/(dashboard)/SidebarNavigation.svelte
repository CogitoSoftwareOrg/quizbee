<script lang="ts">
	import { page } from '$app/state';
	import { House, ChartBar } from 'lucide-svelte';

	const { sidebarOpen = true } = $props<{ sidebarOpen?: boolean }>();

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
	{#if sidebarOpen}
		<ul class="menu menu-vertical w-full gap-1 px-2 pb-2">
			<li class="w-full">
				<a href="/home" class={['text-left', linkClass('home')]}> <House size={20} /> Home </a>
			</li>
			<li class="w-full">
				<a href="/analytics" class={['text-left', linkClass('analytics')]}>
					<ChartBar size={20} /> Analytics
				</a>
			</li>
		</ul>
	{:else}
		<div class="flex w-full flex-col items-center gap-2 py-2">
			<a href="/home" class={iconClass('home')} title="Home">
				<House size={20} />
			</a>
			<a href="/analytics" class={[iconClass('analytics'), 'hidden']} title="Analytics">
				<ChartBar size={20} />
			</a>
		</div>
	{/if}
</nav>
