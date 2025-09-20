import { pb } from '$lib/pb';
import type { QuizAttemptsResponse } from '$lib/pb/pocketbase-types';

class QuizAttemptsStore {
	_quizAttempts: QuizAttemptsResponse[] = $state([]);

	get quizAttempts() {
		return this._quizAttempts;
	}
	set quizAttempts(quizAttempts: QuizAttemptsResponse[]) {
		const sortedQuizAttempts = quizAttempts.toSorted((a, b) => b.created.localeCompare(a.created));
		this._quizAttempts = sortedQuizAttempts;
	}

	async subscribe(userId: string) {
		return pb!.collection('quizAttempts').subscribe(
			'*',
			(e) => {
				const quizAttempt = e.record;
				switch (e.action) {
					case 'create':
						this.quizAttempts.unshift(quizAttempt);
						break;
					case 'update':
						this.quizAttempts =
							this.quizAttempts?.map((q) => (q.id === quizAttempt.id ? quizAttempt : q)) || [];
						break;
					case 'delete':
						this.quizAttempts = this.quizAttempts?.filter((q) => q.id !== quizAttempt.id) || [];
						break;
				}
			},
			{
				filter: `user = "${userId}"`
			}
		);
	}

	unsubscribe() {
		pb!.collection('quizAttempts').unsubscribe();
	}
}

export const quizAttemptsStore = new QuizAttemptsStore();
