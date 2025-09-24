import { computeApiUrl } from '$lib/api/compute-url';
import { pb } from '$lib/pb';
import type { Collections, MessagesResponse } from '$lib/pb/pocketbase-types';
import { nanoid } from '$lib/utils/nanoid';

import type { Sender } from './types';

class MessagesStore {
	_loaded = $state(false);
	_messages: MessagesResponse[] = $state([]);

	get loaded() {
		return this._loaded;
	}

	get messages() {
		return this._messages;
	}
	set messages(messages: MessagesResponse[]) {
		const sortedMessages = messages.toSorted((a, b) => b.created.localeCompare(a.created));
		this._messages = sortedMessages;
	}

	async load(quizAttemptId: string) {
		const messages = await pb!.collection('messages').getFullList({
			filter: `quizAttempt = "${quizAttemptId}"`,
			sort: 'created'
		});
		this.messages = messages;
		this._loaded = true;
	}

	async sendMessage(sender: Sender, attemptId: string, content: string) {
		const clientMsg: MessagesResponse = {
			collectionId: 'messages',
			collectionName: 'messages' as Collections,
			id: nanoid(),
			content,
			created: new Date().toISOString(),
			tokens: 0,
			updated: new Date().toISOString(),
			metadata: {},
			quizAttempt: attemptId,
			role: sender.role as MessagesResponse['role'],
			status: 'client' as MessagesResponse['status']
		};
		this.messages.push(clientMsg);

		const es = new EventSource(
			`${computeApiUrl()}/messages/sse?q=${encodeURIComponent(content)}&attempt=${attemptId}`,
			{
				withCredentials: true
			}
		);
		es.addEventListener('chunk', (e) => {
			const data = JSON.parse(e.data) as { text: string; msg_id: string; i?: number };
			// const list = this.messagesMap.get(roomId);
			// if (!list) return;

			const idx = this._messages.findIndex((m) => m.id === data.msg_id);
			if (idx < 0) return;
			const msg = this._messages[idx];

			if (msg.status !== 'streaming') return;

			// const nextI = data.i ?? ((msg as any)._last_i ?? 0) + 1;
			// if ((msg as any)._last_i && nextI <= (msg as any)._last_i) return;
			// (msg as any)._last_i = nextI;

			msg.content = (msg.content || '') + data.text;
			this._messages[idx] = msg;
		});
		es.addEventListener('error', (e) => {
			console.error(e);
			es.close();
		});
		es.addEventListener('done', () => {
			es.close();
		});
	}

	async subscribe(quizAttemptId: string) {
		return pb!.collection('messages').subscribe(
			'*',
			(e) => {
				const message = e.record;
				switch (e.action) {
					case 'create': {
						const idx = this._messages.findIndex((m) => m.id === message.id);
						if (idx >= 0) {
							this._messages[idx] = message;
						} else {
							this.messages.push(message);
						}
						break;
					}
					case 'update': {
						this.messages = this.messages?.map((m) => (m.id === message.id ? message : m)) || [];
						break;
					}
					case 'delete': {
						this.messages = this.messages?.filter((m) => m.id !== message.id) || [];
						break;
					}
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
