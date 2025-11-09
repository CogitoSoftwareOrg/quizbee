import { pb } from '$lib/pb';
import type { QuizItemsResponse } from '$lib/pb';
import { SvelteMap } from 'svelte/reactivity';

class QuizItemsStore {
	_quizItems: QuizItemsResponse[] = $state([]);

	_quizItemsMap: SvelteMap<string, QuizItemsResponse[]> = $derived.by(() => {
		const m = new SvelteMap<string, QuizItemsResponse[]>();
		this._quizItems.forEach((qi) => {
			const newItems = [...(m.get(qi.quiz) || []), qi];
			newItems.sort((a, b) => a.order - b.order);
			m.set(qi.quiz, newItems);
		});
		return m;
	});

	get quizItems() {
		return this._quizItems;
	}
	get quizItemsMap() {
		return this._quizItemsMap;
	}
	set quizItems(quizItems: QuizItemsResponse[]) {
		const sortedQuizItems = quizItems.toSorted((a, b) => a.order - b.order);
		this._quizItems = sortedQuizItems;
	}

	async subscribe(userId: string) {
		return pb!.collection('quizItems').subscribe(
			'*',
			(e) => {
				const item = e.record;
				switch (e.action) {
					case 'create':
						this._quizItems.unshift(item);
						break;
					case 'update':
						this._quizItems = this._quizItems?.map((qi) => (qi.id === item.id ? item : qi)) || [];
						break;
					case 'delete':
						this._quizItems = this._quizItems?.filter((qi) => qi.id !== item.id) || [];
						break;
				}
			},
			{
				filter: `quiz.author = "${userId}"`
			}
		);
	}

	unsubscribe() {
		pb!.collection('quizItems').unsubscribe();
	}
}

export const quizItemsStore = new QuizItemsStore();
