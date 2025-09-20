import { goto } from '$app/navigation';

import { pb } from '$lib/pb';
import type { UsersResponse } from '$lib/pb/pocketbase-types';
import type { UserExpand } from '$lib/pb/expands';

const EXPAND = [
	'subscriptions_via_user',
	'materials_via_user',
	'quizAttempts_via_user',
	'quizes_via_author',
	'quizes_via_author.quizItems_via_quiz'
].join(',');

export async function load({ depends }) {
	depends('global:user');

	if (!pb!.authStore.isValid) goto('/sign-in');

	const userLoadPromise: Promise<UsersResponse<UserExpand>> = pb!
		.collection('users')
		.authRefresh({
			expand: EXPAND
		})
		.then((res) => res.record as UsersResponse<UserExpand>);
	return { userLoadPromise };
}
