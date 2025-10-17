import { pb } from '$lib/pb/client.js';
import type { QuizesResponse } from '$lib/pb/pocketbase-types';
import type { QuizExpand } from '$lib/pb/expands';

export async function load({ params }) {
	try {
		const quiz: QuizesResponse<QuizExpand> = await pb!
			.collection('quizes')
			.getFirstListItem(`id = "${params.quizId}" || slug = "${params.quizId}"`, {
				expand: 'quizItems_via_quiz'
			});
		return {
			pageQuiz: quiz
		};
	} catch (error) {
		console.error('Failed to load quiz:', error);
		return {
			pageQuiz: null
		};
	}
}
