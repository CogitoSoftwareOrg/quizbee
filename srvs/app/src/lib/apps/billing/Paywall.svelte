<script lang="ts">
	import posthog from 'posthog-js';
	import { page } from '$app/state';
	import { Check, Sparkles } from 'lucide-svelte';

	import { Button } from '@quizbee/ui-svelte-daisy';

	import { computeApiUrl } from '$lib/api/compute-url';

	import { uiStore } from '../users/ui.svelte';

	interface StripePrice {
		lookup: string;
		tariff: string;
		amount: number; // in dollars
	}

	const { stripePrices }: { stripePrices: StripePrice[] } = $props();

	let billingPeriod = $state<'monthly' | 'yearly'>('yearly');
	let loading = $state(false);

	// Create a map of prices by lookup key
	const priceMap = $derived(
		new Map<string, StripePrice>(stripePrices.map((price) => [price.lookup, price]))
	);

	const plans = [
		{
			name: 'Plus',
			description: 'Perfect for serious learners',
			features: [
				'All public quizzes',
				'Up to 1,000 quiz questions/month',
				'Up to 1,000 messages/month',
				'Up to 1GB of file uploads',
				'Real-time difficulty adjustment',
				'Topic refinement'
			],
			lookupPrefix: 'plus_early',
			badge: 'Most Popular'
		},
		{
			name: 'Pro',
			description: 'For power users & professionals',
			features: [
				'Everything in Plus',
				'Up to 2,000 quiz questions/month',
				'Up to 2,000 messages/month',
				'Up to 100GB of file uploads',
				'Priority queue for quiz creation',
				'AI Tutor with full context & Advanced analytics'
			],
			lookupPrefix: 'pro_early',
			highlighted: true,
			badge: 'Maximum Value'
		}
	];

	function calculatePrice(plan: (typeof plans)[number], period: 'monthly' | 'yearly') {
		const monthlyLookup = `${plan.lookupPrefix}_monthly`;
		const yearlyLookup = `${plan.lookupPrefix}_yearly`;

		const monthlyPrice = priceMap.get(monthlyLookup);
		const yearlyPrice = priceMap.get(yearlyLookup);

		if (!monthlyPrice || !yearlyPrice) {
			// Fallback if prices are not loaded yet
			return {
				monthly: 0,
				yearly: null,
				basePrice: 0,
				discount: 0
			};
		}

		// Prices are already 80% of base price (early adopter discount applied)
		// For monthly: price = basePrice * 0.8
		// For yearly: price = basePrice * 0.8 * 0.8 = basePrice * 0.64
		const baseMonthlyPrice = monthlyPrice.amount / 0.8; // Reverse early adopter discount
		const yearlyMonthlyEquivalent = yearlyPrice.amount / 12; // Monthly equivalent of yearly price

		if (period === 'yearly') {
			// Yearly price already includes both discounts (early adopter + yearly)
			// Calculate discount: basePrice * 0.64 vs basePrice = 36% off total
			const discount = Math.round((1 - yearlyPrice.amount / (baseMonthlyPrice * 12)) * 100);

			return {
				monthly: yearlyMonthlyEquivalent,
				yearly: yearlyPrice.amount,
				basePrice: baseMonthlyPrice,
				discount
			};
		}

		// Monthly price already includes early adopter discount (20% off)
		const discount = Math.round((1 - monthlyPrice.amount / baseMonthlyPrice) * 100);

		return {
			monthly: monthlyPrice.amount,
			yearly: null,
			basePrice: baseMonthlyPrice,
			discount
		};
	}

	async function checkoutSession(lookupPrefix: string) {
		loading = true;
		const lookup = `${lookupPrefix}_${billingPeriod}`;

		try {
			posthog.capture('checkout_started', {
				price: lookup,
				return_url: page.url.pathname.slice(1),
				plan: lookupPrefix
			});

			const response = await fetch(`${computeApiUrl()}stripe/checkout`, {
				method: 'POST',
				body: JSON.stringify({ price: lookup, return_url: page.url.pathname.slice(1) }),
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});
			const data = await response.json();
			posthog.capture('checkout_completed', {
				price: lookup,
				...data
			});

			window.location.href = data.url;
			uiStore.setPaywallOpen(false);
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex flex-col gap-2 sm:gap-3">
	<!-- Header -->
	<div class="space-y-1 text-center sm:space-y-2">
		<div class="flex items-center justify-center gap-2">
			<Sparkles class="text-warning size-4 sm:size-5" />
			<span class="badge badge-warning badge-sm sm:badge-md font-semibold">Early Adopter Offer</span
			>
		</div>
		<h2 class="text-xl font-bold sm:text-3xl">Unlock Full Potential</h2>
		<p class="text-base-content/60 mx-auto max-w-lg text-xs sm:text-sm">
			Join the first 500 users and get exclusive early adopter pricing
		</p>
	</div>

	<!-- Period Toggle -->
	<div class="bg-base-200 mx-auto flex items-center gap-2 rounded-full p-1">
		<button
			class={[
				'rounded-full px-3 py-1 text-xs font-semibold transition-all sm:px-6 sm:py-2 sm:text-sm',
				billingPeriod === 'monthly'
					? 'bg-base-100 shadow-md'
					: 'text-base-content/60 hover:text-base-content'
			]}
			onclick={() => {
				billingPeriod = 'monthly';
			}}
		>
			Monthly
		</button>
		<button
			class={[
				'rounded-full px-3 py-1 text-xs font-semibold transition-all sm:px-6 sm:py-2 sm:text-sm',
				billingPeriod === 'yearly'
					? 'bg-base-100 shadow-md'
					: 'text-base-content/60 hover:text-base-content'
			]}
			onclick={() => {
				billingPeriod = 'yearly';
			}}
		>
			Yearly
			{#if billingPeriod === 'yearly'}
				<span class="badge badge-success badge-xs ml-1">-20%</span>
			{/if}
		</button>
	</div>

	<!-- Pricing Cards -->
	<div class="grid grid-cols-1 gap-2 px-1 sm:grid-cols-2 sm:gap-4">
		{#each plans as plan}
			{@const pricing = calculatePrice(plan, billingPeriod)}
			<div
				class={[
					'border-base-200 bg-base-100 relative flex h-full flex-col rounded-xl border p-2.5 shadow-md transition-all duration-300 sm:rounded-2xl sm:p-5',
					plan.highlighted
						? 'ring-primary shadow-xl ring-2'
						: 'hover:border-primary/20 hover:shadow-lg'
				]}
			>
				<!-- Badge -->
				{#if plan.badge}
					<div class="badge badge-xs sm:badge-sm mb-1.5 self-start font-semibold sm:mb-3">
						{plan.badge}
					</div>
				{/if}

				<!-- Plan Name & Description -->
				<div class="mb-2 sm:mb-4">
					<h3 class="mb-0.5 text-lg font-bold sm:mb-1 sm:text-2xl">{plan.name}</h3>
					<p class="text-base-content/60 text-xs sm:text-sm">{plan.description}</p>
				</div>

				<!-- Pricing -->
				<div class="border-base-200 mb-2 border-b pb-2 sm:mb-4 sm:pb-4">
					{#if pricing.monthly > 0}
						<div class="mb-0.5 flex items-baseline gap-1">
							<span class="text-2xl font-bold sm:text-4xl">
								€{Number(pricing.monthly).toFixed(2)}
							</span>
							<span class="text-base-content/60 text-sm sm:text-lg">/mo</span>
						</div>
						{#if pricing.yearly !== null}
							<p class="text-base-content/50 mb-1 text-[11px] sm:text-xs">
								€{pricing.yearly.toFixed(2)} billed annually
							</p>
						{/if}
						<div class="flex items-center gap-1.5">
							<span class="text-base-content/40 text-[11px] line-through sm:text-xs">
								€{pricing.basePrice.toFixed(2)}/mo
							</span>
							<span class="badge badge-success badge-xs sm:badge-sm font-semibold">
								{pricing.discount}% OFF
							</span>
						</div>
					{:else}
						<div class="text-base-content/60 text-sm">Loading prices...</div>
					{/if}
				</div>

				<!-- Features -->
				<ul class="mb-2 flex-1 space-y-1 sm:mb-4 sm:space-y-2">
					{#each plan.features as feature}
						<li class="flex items-start gap-1.5 sm:gap-2">
							<Check class="text-success mt-0.5 size-3 shrink-0 sm:size-4" />
							<span class="text-base-content/70 text-[11px] leading-relaxed sm:text-sm"
								>{feature}</span
							>
						</li>
					{/each}
				</ul>

				<!-- CTA Button -->
				<Button
					style="solid"
					color={plan.highlighted ? 'primary' : 'neutral'}
					size="sm"
					block
					disabled={loading || pricing.monthly === 0}
					onclick={() => checkoutSession(plan.lookupPrefix)}
					class="sm:btn-md"
				>
					{loading ? 'Processing...' : `Get ${plan.name}`}
				</Button>
			</div>
		{/each}
	</div>

	<!-- Bottom Note -->
	<div class="border-base-200 bg-base-200/50 rounded-lg border p-1 text-center">
		<p class="text-base-content/70 text-[10px] leading-relaxed sm:text-xs">
			<span class="font-semibold">Risk-free trial:</span> 14-day money-back guarantee • Cancel anytime
			• Secure checkout powered by Stripe
		</p>
	</div>
</div>
