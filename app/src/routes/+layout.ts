export const ssr = false;
export const prerender = false;

import { pbReady, setPBOnChange } from '$lib/pb';

export async function load() {
	const pb = await pbReady;
	setPBOnChange(pb);
}
