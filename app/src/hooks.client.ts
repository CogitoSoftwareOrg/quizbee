import type { Handle } from '@sveltejs/kit';

import { uiStore } from '$lib/apps/users/ui.svelte.js';
import { pbReady } from '$lib/pb';

export const handle: Handle = async ({ event, resolve }) => {
	await pbReady;
	await uiStore.loadState();

	const response = await resolve(event);
	return response;
};
