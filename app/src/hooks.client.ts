import type { Handle } from '@sveltejs/kit';

import { pbReady, setPBOnChange } from '$lib/pb';

export const handle: Handle = async ({ event, resolve }) => {
	const pb = await pbReady;
	setPBOnChange(pb);

	const response = await resolve(event);
	return response;
};
