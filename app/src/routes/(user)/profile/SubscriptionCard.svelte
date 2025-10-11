<script lang="ts">
	import { Crown, Settings, Rocket } from 'lucide-svelte';
	import Button from '$lib/ui/Button.svelte';
	import { postApi } from '$lib/api/call-api';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	const subscription = $derived(subscriptionStore.subscription);
	const paid = $derived(subscription?.status === 'active' && subscription.tariff !== 'free');
</script>

<div class="card bg-base-100 shadow-lg">
	<div class="card-body">
		<div class="flex items-center justify-between">
			<span class="text-sm font-semibold">Subscription</span>
			{#if paid}
				<div class="badge badge-success badge-sm gap-1">
					<Crown class="h-3 w-3" />
					Premium
				</div>
			{:else}
				<div class="badge badge-ghost badge-sm">Free</div>
			{/if}
		</div>

		<div class="mt-3">
			{#if paid}
				<Button
					onclick={async () => {
						const response = await postApi('billing/portal', {
							return_url: 'profile'
						});
						window.location.href = response.url;
					}}
					style="soft"
					size="sm"
					block
				>
					<Settings class="h-4 w-4" />
					Manage Subscription
				</Button>
			{:else}
				<Button onclick={() => uiStore.setPaywallOpen(true)} size="sm" block>
					<Rocket class="h-4 w-4" />
					Upgrade to Premium
				</Button>
			{/if}
		</div>
	</div>
</div>
