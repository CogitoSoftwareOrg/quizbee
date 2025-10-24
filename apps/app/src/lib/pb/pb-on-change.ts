import { userStore } from '$lib/apps/users/user.svelte';

import type { UsersResponse } from './pocketbase-types';
import type { UserExpand } from './expands';
import { pb } from './client';

// import { settingsProvider } from './settings.svelte';
// import { uiProvider } from './ui.svelte';

pb!.authStore.onChange((token, record) => {
	if (record && pb!.authStore.isValid) {
		console.log('rec', record);
		try {
			const user = record as UsersResponse<unknown, UserExpand>;
			userStore.user = user;
			userStore.token = token;

			setPBCookie();
		} catch (error) {
			console.error('Failed to parse user data:', error);
		}
	} else {
		userStore.user = null;
		userStore.token = null;
		// settingsProvider.clear();
		// uiProvider.clear();
	}
}, false);

function setPBCookie() {
	const host = typeof window !== 'undefined' ? window.location.hostname : '';
	const isQuizbee = host.endsWith('quizbee.academy');
	const domain = isQuizbee ? '.quizbee.academy' : undefined;

	document.cookie = pb!.authStore.exportToCookie({
		httpOnly: false,
		secure: true,
		sameSite: 'Lax',
		domain,
		path: '/'
	});
}
