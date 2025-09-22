export const ssr = false;
export const prerender = false;

import { uiStore } from '$lib/apps/users/ui.svelte';

export const load = async () => {
	await uiStore.loadState();
};
