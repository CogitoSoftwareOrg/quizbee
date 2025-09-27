export const ssr = false;
export const prerender = false;

import { uiStore } from '$lib/apps/users/ui.svelte';
import posthog from 'posthog-js';

export const load = async () => {
	await uiStore.loadState();

	posthog.init('phc_d13j4oIyubPnDVvRyALOBtoTqj0jkXcoJwDGeYjlCXV', {
		api_host: 'https://eu.i.posthog.com',
		defaults: '2025-05-24'
	});
};
