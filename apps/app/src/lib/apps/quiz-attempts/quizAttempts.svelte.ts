import { pb } from '$lib/pb';
import type { QuizAttemptsResponse } from '@quizbee/pb-types';

class QuizAttemptsStore {
	private _quizAttempts: QuizAttemptsResponse[] = $state([]);

	get quizAttempts() {
		return this._quizAttempts;
	}
	set quizAttempts(quizAttempts: QuizAttemptsResponse[]) {
		const sortedQuizAttempts = quizAttempts.toSorted((a, b) => b.created.localeCompare(a.created));
		this._quizAttempts = sortedQuizAttempts;
	}
	add(quizAttempt: QuizAttemptsResponse) {
		this._quizAttempts.unshift(quizAttempt);
	}

	async subscribe(userId: string) {
		console.log('subscribing to quizAttempts', userId);
		return pb!.collection('quizAttempts').subscribe(
			'*',
			(e) => {
				console.log('quizAttempts', e);
				const quizAttempt = e.record;
				switch (e.action) {
					case 'create': {
						this._quizAttempts.unshift(quizAttempt);
						break;
					}
					case 'update': {
						this._quizAttempts =
							this._quizAttempts?.map((q) => (q.id === quizAttempt.id ? quizAttempt : q)) || [];
						break;
					}
					case 'delete': {
						this._quizAttempts = this._quizAttempts?.filter((q) => q.id !== quizAttempt.id) || [];
						break;
					}
				}
			},
			{
				filter: `user = "${userId}"`
			}
		);
	}

	unsubscribe() {
		console.log('unsubscribing from quizAttempts');
		pb!.collection('quizAttempts').unsubscribe();
	}
}

export const quizAttemptsStore = new QuizAttemptsStore();
