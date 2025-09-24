<script lang="ts">
	import { Settings } from 'lucide-svelte';
	import type { ClassValue } from 'svelte/elements';

	import { pb } from '$lib/pb';
	import Man from '$lib/assets/images/Man.jpg';
	import { userStore } from '$lib/apps/users/user.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	interface Props {
		class?: ClassValue;
	}
	let { class: className }: Props = $props();

	const user = $derived(userStore.user);
	const avatar = $derived(user?.avatar ? pb!.files.getURL(user, user.avatar) : Man);
</script>

<a
	class={[
		'border-base-200 flex cursor-pointer items-center justify-center gap-2 border-t p-1',
		className
	]}
	href="/profile"
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
			<Settings class="size-6" />
		</div>
	{/if}
</a>
