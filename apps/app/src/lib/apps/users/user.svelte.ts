import type { AuthRecord } from 'pocketbase';

import { pb } from '$lib/pb';
import type { UsersResponse } from '$lib/pb';
import type { UserExpand } from '$lib/pb/expands';
import type { Sender } from '$lib/apps/messages/types';
import Man from '$lib/assets/images/Man.jpg';
class UserStore {
	_loaded = $state(false);

	_user: UsersResponse<unknown, UserExpand> | null = $state(null);
	token: string | null = $state(null);

	get loaded() {
		return this._loaded;
	}
	setLoaded() {
		this._loaded = true;
	}
	get user() {
		return this._user;
	}
	set user(user: UsersResponse<unknown, UserExpand> | null) {
		this._user = user;
	}

	sender: Sender = $derived({
		id: this.user?.id || '',
		avatar: this.user?.avatar ? pb?.files.getURL(this.user, this.user.avatar) || Man : Man,
		name: this.user?.name || 'Name',
		role: 'user'
	});

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
