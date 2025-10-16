export const prerender = false;

import { pb } from '$lib/pb';
import type { UsersResponse } from '$lib/pb/pocketbase-types';
import type { QuizExpand, UserExpand } from '$lib/pb/expands';

import { materialsStore } from '$lib/apps/materials/materials.svelte';
import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
import { userStore } from '$lib/apps/users/user.svelte';
import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
import { goto } from '$app/navigation';

const EXPAND = [
	'subscriptions_via_user',
	'materials_via_user',
	'quizAttempts_via_user',
	'quizes_via_author',
	'quizes_via_author.quizItems_via_quiz'
].join(',');

export async function load({ depends }) {
	depends('global:user');

	if (!pb?.authStore.isValid) await goto('/sign-in', { replaceState: true });

	const userLoadPromise: Promise<UsersResponse<unknown, UserExpand> | null> = pb!
		.collection('users')
		.authRefresh({
			expand: EXPAND,
			requestKey: null
		})
		.then((res) => {
			const user = res.record as UsersResponse<unknown, UserExpand>;
			const subscription = user.expand.subscriptions_via_user?.[0] || null;
			const materials = user.expand.materials_via_user || [];
			const quizAttempts = user.expand.quizAttempts_via_user || [];
			const quizes = user.expand.quizes_via_author || [];
			const quizItems = quizes.map((q) => q.expand.quizItems_via_quiz || []).flat();

			materialsStore.materials = materials;
			quizAttemptsStore.quizAttempts = quizAttempts;
			subscriptionStore.subscription = subscription;

			quizItemsStore.quizItems = quizItems;

			quizes.forEach((q) => {
				q.expand = {} as QuizExpand;
			});
			quizesStore.quizes = quizes;

			user.expand = {} as UserExpand;
			userStore.user = user;

			userStore.setLoaded();
			return user;
		})
		.catch(async (error) => {
			console.error('Failed to load user:', error);
			await goto('/sign-in', { replaceState: true });
			return null;
		});
	return { userLoadPromise };
}
