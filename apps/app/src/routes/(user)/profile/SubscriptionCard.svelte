<script lang="ts">
	import { Crown, Settings, Rocket } from 'lucide-svelte';

	import { Button } from '@cogisoft/ui-svelte-daisy';

	import { postApi } from '$lib/api/call-api';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	const subscription = $derived(subscriptionStore.subscription);
	const paid = $derived(subscription?.status === 'active' && subscription.tariff !== 'free');
	const quizItemsUsage = $derived(subscription?.quizItemsUsage ?? 0);
	const quizItemsLimit = $derived(subscription?.quizItemsLimit ?? 0);
	const questionsProgress = $derived(
		quizItemsLimit > 0 ? (quizItemsUsage / quizItemsLimit) * 100 : 0
	);
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

		<!-- Questions Usage Widget -->
		{#if quizItemsLimit > 0}
			<div class="mt-4 space-y-2">
				<div class="flex items-center justify-between">
					<span class="text-xs font-semibold">Questions</span>
					<span class="text-base-content/70 text-xs font-medium">
						{quizItemsUsage} / {quizItemsLimit}
					</span>
				</div>
				<progress
					class="progress {questionsProgress >= 90
						? 'progress-error'
						: questionsProgress >= 70
							? 'progress-warning'
							: 'progress-primary'}"
					value={questionsProgress}
					max="100"
				></progress>
				<div class="flex items-center justify-between gap-2">
					<div class="text-base-content/60 text-xs">
						{Math.round(questionsProgress)}% used
					</div>
					<div class="text-base-content/60 text-xs">
						{quizItemsLimit - quizItemsUsage} remaining
					</div>
				</div>
			</div>
		{/if}

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
