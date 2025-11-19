export const ssr = false;
export const prerender = false;

import { pb } from '$lib/pb';
import type {
	UsersResponse,
	QuizesResponse,
	QuizAttemptsResponse,
	QuizItemsResponse,
	QuizExpand,
	UserExpand,
	QuizAttemptExpand
} from '@quizbee/pb-types';

import { materialsStore } from '$lib/apps/materials/materials.svelte';
import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
import { userStore } from '$lib/apps/users/user.svelte';
import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
import { goto } from '$app/navigation';

export async function load({ depends }) {
	depends('global:user');

	const userLoadPromise: Promise<UsersResponse<unknown, UserExpand> | null> = pb!
		.collection('users')
		.authRefresh({
			requestKey: null
		})
		.then(async (res) => {
			const user = res.record as UsersResponse<unknown, UserExpand>;
			userStore.user = user;

			// Load related data in separate calls to avoid storage quota issues
			const [subscription, materials, quizAttempts, quizesWithExpand] = await Promise.all([
				pb!
					.collection('subscriptions')
					.getFirstListItem(`user="${user.id}"`)
					.catch(() => null),
				pb!
					.collection('materials')
					.getFullList({ filter: `user="${user.id}"`, sort: '-created' })
					.catch(() => []),
				pb!
					.collection('quizAttempts')
					.getFullList<QuizAttemptsResponse<unknown, unknown, QuizAttemptExpand>>({
						filter: `user="${user.id}"`,
						expand: 'quiz,quiz.quizItems_via_quiz',
						sort: '-created'
					})
					.catch(() => [] as QuizAttemptsResponse<unknown, unknown, QuizAttemptExpand>[]),
				pb!
					.collection('quizes')
					.getFullList<QuizesResponse<unknown, unknown, unknown, QuizExpand>>({
						filter: `author="${user.id}"`,
						expand: 'quizItems_via_quiz',
						sort: '-created'
					})
					.catch(() => [] as QuizesResponse<unknown, unknown, unknown, QuizExpand>[])
			]);

			// Collect quizItems from both author quizes and quiz attempts
			const authorQuizItems = quizesWithExpand
				.map((q) => q.expand?.quizItems_via_quiz || [])
				.flat();
			const attemptQuizItems = quizAttempts
				.map((attempt) => {
					const quiz = attempt.expand?.quiz as
						| QuizesResponse<unknown, unknown, unknown, QuizExpand>
						| undefined;
					return quiz?.expand?.quizItems_via_quiz || [];
				})
				.flat();

			// Combine and deduplicate quizItems
			const allQuizItems = [...authorQuizItems, ...attemptQuizItems];
			const uniqueQuizItems = Array.from(
				new Map(allQuizItems.map((item) => [item.id, item])).values()
			);

			materialsStore.materials = materials;
			quizAttemptsStore.quizAttempts = quizAttempts;
			subscriptionStore.subscription = subscription;
			quizItemsStore.quizItems = uniqueQuizItems;

			// Remove expand from quizes to avoid storing too much data
			const quizes = quizesWithExpand.map((q) => {
				const quiz = { ...q };
				quiz.expand = {} as QuizExpand;
				return quiz;
			}) as QuizesResponse<QuizExpand>[];
			quizesStore.quizes = quizes;

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
