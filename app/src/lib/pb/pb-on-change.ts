import type { TypedPocketBase, UsersResponse } from './pocketbase-types';
import type { UserExpand } from './expands';

// import { settingsProvider } from './settings.svelte';
// import { userProvider } from './user.svelte';
// import { uiProvider } from './ui.svelte';

export function setPBOnChange(pb: TypedPocketBase) {
	pb.authStore.onChange((_, rec) => {
		if (rec && pb.authStore.isValid) {
			try {
				const user = rec as UsersResponse<UserExpand>;
				console.log('user', user);
				// userProvider.user = user;
				// userProvider.token = pb.authStore.token;

				setPBCookie(pb);
			} catch (error) {
				console.error('Failed to parse user data:', error);
				// userProvider.user = null;
			}
		} else {
			// userProvider.user = null;
			// userProvider.token = null;
			// settingsProvider.clear();
			// uiProvider.clear();
		}
	}, false);
}

function setPBCookie(pb: TypedPocketBase) {
	const host = typeof window !== 'undefined' ? window.location.hostname : '';
	const isGrowplex = host.endsWith('.growplex.dev');
	const domainAttr = isGrowplex ? 'Domain=.growplex.dev' : undefined;
	document.cookie = [
		`pb_token=${pb.authStore.token}`,
		domainAttr,
		'Secure',
		'Path=/',
		'Max-Age=600',
		'SameSite=None'
	]
		.filter(Boolean)
		.join('; ');
}
