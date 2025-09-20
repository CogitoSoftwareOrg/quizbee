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
			const user = record as UsersResponse<UserExpand>;
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
	const isQuizbee = host.endsWith('quizbee.cogitosoftware.nl');
	const domainAttr = isQuizbee ? 'Domain=.cogitosoftware.nl' : undefined;
	document.cookie = [
		`pb_token=${pb!.authStore.token}`,
		domainAttr,
		'Secure',
		'Path=/',
		'Max-Age=600',
		'SameSite=None'
	]
		.filter(Boolean)
		.join('; ');
}
