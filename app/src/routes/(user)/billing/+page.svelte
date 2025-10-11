<script lang="ts">
	import { page } from '$app/state';

	import { computeApiUrl } from '$lib/api/compute-url';
	import Button from '$lib/ui/Button.svelte';

	type Price = 'plus_monthly' | 'pro_monthly' | 'plus_yearly' | 'pro_yearly';

	const prices = [
		{
			label: 'Plus Monthly',
			price: 'plus_monthly'
		},

		{
			label: 'Pro Monthly',
			price: 'pro_monthly'
		},
		{
			label: 'Plus Yearly',
			price: 'plus_yearly'
		},
		{
			label: 'Pro Yearly',
			price: 'pro_yearly'
		}
	];

	let loading = $state(false);

	async function checkoutSession(price: Price) {
		loading = true;
		try {
			const response = await fetch(`${computeApiUrl()}billing/stripe/checkout`, {
				method: 'POST',
				body: JSON.stringify({ price, return_url: page.url.pathname.slice(1) }),
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});
			const data = await response.json();
			console.log(data);
			window.location.href = data.url;
		} finally {
			loading = false;
		}
	}
</script>

<div>
	<h1>Billing</h1>
	<div class="flex gap-4">
		{#each prices as price}
			<Button onclick={() => checkoutSession(price.price as Price)} disabled={loading}>
				{price.label}
			</Button>
		{/each}
	</div>
</div>
