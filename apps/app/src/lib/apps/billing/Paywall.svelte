<script lang="ts">
	import posthog from 'posthog-js';
	import { page } from '$app/state';
	import { Check, Sparkles } from 'lucide-svelte';

	import { Button } from '@quizbee/ui-svelte-daisy';
	import { computeApiUrl } from '$lib/api/compute-url';

	type Price = 'plus_monthly' | 'pro_monthly' | 'plus_yearly' | 'pro_yearly';

	let billingPeriod = $state<'monthly' | 'yearly'>('yearly');
	let loading = $state(false);

	const plans = [
		{
			name: 'Plus',
			basePrice: 7.99,
			description: 'Perfect for serious learners',
			features: [
				'All public quizzes',
				'Up to 1,000 quiz questions/month',
				'Up to 1,000 messages/month',
				'Up to 1GB of file uploads',
				'Real-time difficulty adjustment',
				'Topic refinement'
			],
			priceKey: 'plus',
			badge: 'Most Popular'
		},
		{
			name: 'Pro',
			basePrice: 15.99,
			description: 'For power users & professionals',
			features: [
				'Everything in Plus',
				'Up to 2,000 quiz questions/month',
				'Up to 2,000 messages/month',
				'Up to 100GB of file uploads',
				'Priority queue for quiz creation',
				'AI Tutor with full context & Advanced analytics'
			],
			priceKey: 'pro',
			highlighted: true,
			badge: 'Maximum Value'
		}
	];

	function calculatePrice(basePrice: number, period: 'monthly' | 'yearly') {
		const earlyAdopterDiscount = 0.2; // 20% off
		const yearlyDiscount = 0.2; // Additional 20% off

		if (period === 'yearly') {
			return {
				monthly: basePrice * (1 - (yearlyDiscount + earlyAdopterDiscount)),
				yearly: basePrice * (1 - (yearlyDiscount + earlyAdopterDiscount)) * 12,
				discount: 40
			};
		}

		return {
			monthly: basePrice * (1 - earlyAdopterDiscount),
			yearly: null,
			discount: 20
		};
	}

	async function checkoutSession(priceKey: string) {
		loading = true;
		const price: Price = `${priceKey}_${billingPeriod}` as Price;

		try {
			posthog.capture('checkout_started', {
				price,
				return_url: page.url.pathname.slice(1),
				plan: priceKey
			});

			const response = await fetch(`${computeApiUrl()}stripe/checkout`, {
				method: 'POST',
				body: JSON.stringify({ price, return_url: page.url.pathname.slice(1) }),
				headers: {
					'Content-Type': 'application/json'
				},
				credentials: 'include'
			});
			const data = await response.json();
			posthog.capture('checkout_completed', {
				price,
				...data
			});

			window.location.href = data.url;
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex max-h-[90vh] flex-col gap-2 overflow-y-auto p-2 sm:gap-3 sm:p-4">
	<!-- Header -->
	<div class="space-y-1.5 text-center sm:space-y-2">
		<div class="flex items-center justify-center gap-2">
			<Sparkles class="text-warning size-4 sm:size-5" />
			<span class="badge badge-warning badge-sm sm:badge-md font-semibold">Early Adopter Offer</span
			>
		</div>
		<h2 class="text-2xl font-bold sm:text-3xl">Unlock Full Potential</h2>
		<p class="text-base-content/60 mx-auto max-w-lg text-xs sm:text-sm">
			Join the first 500 users and get exclusive early adopter pricing
		</p>
	</div>

	<!-- Period Toggle -->
	<div class="bg-base-200 mx-auto flex items-center gap-2 rounded-full p-1 sm:gap-3">
		<button
			class={[
				'rounded-full px-4 py-1.5 text-xs font-semibold transition-all sm:px-6 sm:py-2 sm:text-sm',
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
				'rounded-full px-4 py-1.5 text-xs font-semibold transition-all sm:px-6 sm:py-2 sm:text-sm',
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
	<div class="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4">
		{#each plans as plan}
			{@const pricing = calculatePrice(plan.basePrice, billingPeriod)}
			<div
				class={[
					'border-base-200 bg-base-100 relative flex h-full flex-col rounded-xl border p-3 shadow-md transition-all duration-300 sm:rounded-2xl sm:p-5',
					plan.highlighted
						? 'ring-primary shadow-xl ring-2'
						: 'hover:border-primary/20 hover:shadow-lg'
				]}
			>
				<!-- Badge -->
				{#if plan.badge}
					<div class="badge badge-xs sm:badge-sm mb-2 self-start font-semibold sm:mb-3">
						{plan.badge}
					</div>
				{/if}

				<!-- Plan Name & Description -->
				<div class="mb-3 sm:mb-4">
					<h3 class="mb-1 text-xl font-bold sm:text-2xl">{plan.name}</h3>
					<p class="text-base-content/60 text-xs sm:text-sm">{plan.description}</p>
				</div>

				<!-- Pricing -->
				<div class="border-base-200 mb-3 border-b pb-3 sm:mb-4 sm:pb-4">
					<div class="mb-0.5 flex items-baseline gap-1 sm:mb-1">
						<span class="text-3xl font-bold sm:text-4xl">${pricing.monthly.toFixed(2)}</span>
						<span class="text-base-content/60 text-base sm:text-lg">/mo</span>
					</div>
					{#if pricing.yearly}
						<p class="text-base-content/50 mb-1.5 text-xs">
							${pricing.yearly.toFixed(2)} billed annually
						</p>
					{/if}
					<div class="flex items-center gap-1.5">
						<span class="text-base-content/40 text-xs line-through">
							${plan.basePrice}/mo
						</span>
						<span class="badge badge-success badge-xs sm:badge-sm font-semibold">
							{pricing.discount}% OFF
						</span>
					</div>
				</div>

				<!-- Features -->
				<ul class="mb-3 flex-1 space-y-1.5 sm:mb-4 sm:space-y-2">
					{#each plan.features as feature}
						<li class="flex items-start gap-2">
							<Check class="text-success mt-0.5 size-3.5 shrink-0 sm:size-4" />
							<span class="text-base-content/70 text-xs leading-relaxed sm:text-sm">{feature}</span>
						</li>
					{/each}
				</ul>

				<!-- CTA Button -->
				<Button
					style="solid"
					color={plan.highlighted ? 'primary' : 'neutral'}
					size="md"
					block
					disabled={loading}
					onclick={() => checkoutSession(plan.priceKey)}
					class="sm:btn-lg"
				>
					{loading ? 'Processing...' : `Get ${plan.name}`}
				</Button>
			</div>
		{/each}
	</div>

	<!-- Bottom Note -->
	<div class="border-base-200 bg-base-200/50 rounded-lg border p-2 text-center sm:p-3">
		<p class="text-base-content/70 text-[10px] leading-relaxed sm:text-xs">
			<span class="font-semibold">Risk-free trial:</span> 14-day money-back guarantee • Cancel anytime
			• Secure checkout powered by Stripe
		</p>
	</div>
</div>
