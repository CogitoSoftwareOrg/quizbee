<script lang="ts">
	import { ChevronUp } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import type { ClassValue } from 'svelte/elements';
	import { page } from '$app/state';

	import { pb } from '$lib/pb';
	import Button from '$lib/ui/Button.svelte';
	import Man from '$lib/assets/images/Man.jpg';
	import { clickOutside } from '$lib/actions/click-outside';
	import { userStore } from '$lib/apps/users/user.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	interface Props {
		class?: ClassValue;
	}
	let { class: className }: Props = $props();

	let open = $state(false);

	const user = $derived(userStore.user);
	const avatar = $derived(user?.avatar ? pb!.files.getURL(user, user.avatar) : Man);

	function handleLogout() {
		pb!.authStore.clear();
		goto('/sign-in');
	}
</script>

<!-- TRIGGER -->
<button
	use:clickOutside={{ callback: () => (open = false) }}
	class={[
		'dropdown dropdown-top border-base-200 flex cursor-pointer items-center gap-2 border-t p-1',
		uiStore.globalSidebarOpen
			? 'dropdown-center dropdown-hover justify-between'
			: 'dropdown-right justify-center',
		className
	]}
	class:dropdown-open={open}
	onclick={() => (open = true)}
>
	<div class="border-base-300 size-10 overflow-hidden rounded-full">
		<img src={avatar} alt="avatar" />
	</div>

	{#if uiStore.globalSidebarOpen}
		<div class="flex h-full flex-1 flex-col gap-1">
			<p class="truncate text-sm font-semibold">{user?.name || user?.email}</p>
			<p class="badge-primary badge badge-sm font-semibold">:3</p>
		</div>

		<div>
			<ChevronUp class="size-6" />
		</div>
	{/if}

	<!-- MENU -->
	<ul
		class={[
			'dropdown-content menu rounded-box border-base-200 space-y-1 border p-2 shadow',
			uiStore.globalSidebarOpen ? 'w-full' : 'w-52'
		]}
	>
		<li>
			<Button
				size="sm"
				style={page.url.pathname.endsWith('/profile') ? 'soft' : 'ghost'}
				color={page.url.pathname.endsWith('/profile') ? 'primary' : 'neutral'}
				href="/profile"
			>
				Profile
			</Button>
			<Button
				size="sm"
				style={page.url.pathname.endsWith('/billing') ? 'soft' : 'ghost'}
				color={page.url.pathname.endsWith('/billing') ? 'primary' : 'neutral'}
				href="/billing"
			>
				Billing
			</Button>
		</li>
		<li>
			<Button size="sm" style="soft" color="error" onclick={handleLogout}>Logout</Button>
		</li>
	</ul>
</button>
