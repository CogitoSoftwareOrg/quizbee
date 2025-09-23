import type { Handle } from '@sveltejs/kit';

import { pbReady } from '$lib/pb';

export const handle: Handle = async ({ event, resolve }) => {
	await pbReady;

	const response = await resolve(event);
	return response;
};
