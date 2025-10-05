import { pb } from '$lib/pb/client.js';

export async function load({ params }) {
	try {
		const quiz = await pb!.collection('quizes').getOne(params.quizId);
		console.log('quiz', quiz);
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
