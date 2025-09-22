import { goto } from '$app/navigation';

import { pb } from '$lib/pb';
import type { UsersResponse } from '$lib/pb/pocketbase-types';
import type { UserExpand } from '$lib/pb/expands';
import { error } from '@sveltejs/kit';

const EXPAND = [
	'subscriptions_via_user',
	'materials_via_user',
	'quizAttempts_via_user',
	'quizes_via_author',
	'quizes_via_author.quizItems_via_quiz'
].join(',');

export async function load({ depends }) {
	depends('global:user');

	if (!pb?.authStore.isValid) await goto('/sign-in');

	const userLoadPromise: Promise<UsersResponse<unknown, UserExpand>> = pb!
		.collection('users')
		.authRefresh({
			expand: EXPAND
		})
		.then((res) => res.record as UsersResponse<unknown, UserExpand>)
		.catch(async () => {
			console.error('Failed to load user:', error);
			await goto('/sign-in');
		});
	return { userLoadPromise };
}
