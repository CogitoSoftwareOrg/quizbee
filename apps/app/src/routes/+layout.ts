export const ssr = false;
export const prerender = true;

import posthog from 'posthog-js';
import { env } from '$env/dynamic/public';

import { uiStore } from '$lib/apps/users/ui.svelte';

export const load = async () => {
	await uiStore.loadState();

	const ENV = env.PUBLIC_ENV;
	const POSTHOG_TOKEN =
		ENV === 'production'
			? env.PUBLIC_POSTHOG_PROD
			: ENV === 'quality-assurance'
				? env.PUBLIC_POSTHOG_QA
				: env.PUBLIC_POSTHOG_LOCAL;

	if (POSTHOG_TOKEN)
		posthog.init(POSTHOG_TOKEN, {
			api_host: 'https://eu.i.posthog.com',
			defaults: '2025-05-24'
		});
};
