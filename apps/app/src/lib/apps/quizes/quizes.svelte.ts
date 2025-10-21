import { pb, type QuizExpand } from '$lib/pb';
import type { QuizesResponse } from '$lib/pb/pocketbase-types';

class QuizesStore {
	_quizes: QuizesResponse<QuizExpand>[] = $state([]);

	get quizes() {
		return this._quizes;
	}
	set quizes(quizes: QuizesResponse<QuizExpand>[]) {
		const sortedQuizes = quizes.toSorted((a, b) => b.created.localeCompare(a.created));
		this._quizes = sortedQuizes;
	}

	async subscribe(userId: string) {
		return pb!.collection('quizes').subscribe(
			'*',
			(e) => {
				const quiz = e.record as QuizesResponse<QuizExpand>;
				switch (e.action) {
					case 'create':
						this.quizes.unshift(quiz);
						break;
					case 'update':
						this.quizes = this.quizes?.map((q) => (q.id === quiz.id ? quiz : q)) || [];
						break;
					case 'delete':
						this.quizes = this.quizes?.filter((q) => q.id !== quiz.id) || [];
						break;
				}
			},
			{
				filter: `author = "${userId}"`
			}
		);
	}

	unsubscribe() {
		pb!.collection('quizes').unsubscribe();
	}
}

export const quizesStore = new QuizesStore();
