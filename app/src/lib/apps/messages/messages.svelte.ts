import { pb } from '$lib/pb';
import type { MessagesResponse } from '$lib/pb/pocketbase-types';

class MessagesStore {
	_messages: MessagesResponse[] = $state([]);

	get messages() {
		return this._messages;
	}
	set messages(messages: MessagesResponse[]) {
		const sortedMessages = messages.toSorted((a, b) => b.created.localeCompare(a.created));
		this._messages = sortedMessages;
	}

	async subscribe(quizAttemptId: string) {
		return pb!.collection('messages').subscribe(
			'*',
			(e) => {
				const message = e.record;
				switch (e.action) {
					case 'create':
						this.messages.unshift(message);
						break;
					case 'update':
						this.messages = this.messages?.map((m) => (m.id === message.id ? message : m)) || [];
						break;
					case 'delete':
						this.messages = this.messages?.filter((m) => m.id !== message.id) || [];
						break;
				}
			},
			{
				filter: `quizAttempt = "${quizAttemptId}"`
			}
		);
	}

	unsubscribe() {
		pb!.collection('messages').unsubscribe();
	}
}

export const messagesStore = new MessagesStore();
