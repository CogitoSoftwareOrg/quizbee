export const ssr = false;
export const prerender = true;

import Stripe from 'stripe';
import { STRIPE_API_KEY } from '$env/static/private';

const stripe = new Stripe(STRIPE_API_KEY);

export const load = async () => {
	const prices = await stripe.prices.list({
		lookup_keys: [
			'plus_early_monthly',
			'plus_early_yearly',
			'pro_early_monthly',
			'pro_early_yearly'
		]
	});

	return {
		stripePrices: prices.data.map((price) => ({
			lookup: price.lookup_key,
			tariff: price.lookup_key!.split('_')[0] ?? '',
			amount: (price.unit_amount ?? 0) / 100
		}))
	};
};
