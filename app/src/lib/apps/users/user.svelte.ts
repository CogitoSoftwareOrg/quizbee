import type { AuthRecord } from 'pocketbase';

import { pb } from '$lib/pb';
import type { UsersResponse } from '$lib/pb/pocketbase-types';
import type { UserExpand } from '$lib/pb/expands';

// import Man from '$lib/assets/Man.jpg';
// import { settingsProvider } from './settings.svelte';
// import type { Sender } from '../chats/types';

class UserStore {
	_user: UsersResponse<UserExpand> | null = $state(null);
	token: string | null = $state(null);

	get user() {
		return this._user;
	}
	set user(user: UsersResponse<UserExpand> | null) {
		if (user?.expand) user.expand = undefined;
		this._user = user;
	}

	// sender: Sender = $derived({
	// 	id: this.user?.id || '',
	// 	avatar: this.user?.avatar ? pb.files.getURL(this.user, this.user.avatar) : Man,
	// 	name: this.user?.name || 'Name',
	// 	role: this.user?.guest ? 'guest' : 'admin'
	// });

	async subscribe(userId: string) {
		return pb!.collection('users').subscribe(userId, (e) => {
			console.log(e);
			switch (e.action) {
				case 'update':
					pb!.authStore.save(pb!.authStore.token, e.record as AuthRecord);
					break;
				case 'delete':
					pb!.authStore.clear();
					break;
			}
		});
	}

	unsubscribe(userId: string) {
		pb!.collection('users').unsubscribe(userId);
	}
}

export const userStore = new UserStore();
