export const ssr = false;
export const prerender = false;

import { pbReady } from '$lib/pb/client';

export async function load() {
	await pbReady;

	return {
		ok: true
	};
}
