<script lang="ts">
	import { Settings } from 'lucide-svelte';
	import type { ClassValue } from 'svelte/elements';

	import { pb } from '$lib/pb';
	import Man from '$lib/assets/images/Man.jpg';
	import { userStore } from '$lib/apps/users/user.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import { subscriptionStore } from '../billing/subscriptions.svelte';

	interface Props {
		class?: ClassValue;
		expanded?: boolean;
	}
	let { class: className, expanded = false }: Props = $props();

	const user = $derived(userStore.user);
	const avatar = $derived(user?.avatar ? pb!.files.getURL(user, user.avatar) : Man);
	const sub = $derived(subscriptionStore.subscription);
</script>

<div class={className}>
	<a
		class={['border-base-200 flex cursor-pointer items-center justify-center gap-2 border-t p-1']}
		href="/profile"
	>
		<div
			class:size-8={!expanded}
			class:size-10={expanded}
			class="border-base-300 overflow-hidden rounded-full"
		>
			<img src={avatar} alt="avatar" />
		</div>

		{#if expanded}
			<div class="flex h-full flex-1 flex-col gap-1">
				<p class="truncate text-sm font-semibold">{user?.name || user?.email}</p>

				<div class="flex items-center gap-1">
					<p class="badge-primary badge badge-sm font-semibold">{sub?.tariff}</p>
					<!-- <p class="badge-primary badge badge-sm font-semibold">
				q: <span class="text-xs">{sub?.quizItemsUsage} / {sub?.quizItemsLimit}</span>
				</p> -->
				</div>
			</div>

			<div>
				<Settings class="size-6" />
			</div>
		{/if}
	</a>
</div>
