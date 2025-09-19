import { goto } from '$app/navigation';

import { pb } from '$lib/pb';

export async function load() {
	if (!pb!.authStore.isValid) goto('/sign-in');

	// const userPromise = pb!.collection('users').authRefresh();
	// return { userPromise };
	return {};
}
