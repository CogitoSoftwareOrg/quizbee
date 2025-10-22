import { postApi } from '$lib/api/call-api';
import { computeApiUrl } from '$lib/api/compute-url';
import { pb } from '$lib/pb';
import type { Collections, MessagesResponse } from '@quizbee/pb-types';
import { nanoid } from '$lib/utils/nanoid';

import type { Sender } from '../types';

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
		this._messages = messages;
	}

	async load(quizAttemptId: string) {
		const messages = await pb!.collection('messages').getFullList({
			filter: `quizAttempt = "${quizAttemptId}"`,
			sort: 'created'
		});
		this.messages = messages;
		this._loaded = true;
	}

	async sendMessage(
		sender: Sender,
		content: string,
		attemptId: string,
		itemId: string,
		mode: 'sse' | 'post' = 'sse'
	) {
		const clientMsg: MessagesResponse = {
			collectionId: 'messages',
			collectionName: 'messages' as Collections,
			id: nanoid(),
			content,
			created: new Date().toISOString(),
			tokens: 0,
			updated: new Date().toISOString(),
			metadata: { itemId },
			quizAttempt: attemptId,
			role: sender.role as MessagesResponse['role'],
			status: 'onClient' as MessagesResponse['status']
		};
		this.messages.push(clientMsg);

		if (mode === 'sse') {
			const es = new EventSource(
				`${computeApiUrl()}messages/sse?q=${encodeURIComponent(content)}&attempt=${attemptId}&item=${itemId}`,
				{
					withCredentials: true
				}
			);
			es.addEventListener('chunk', (e) => {
				const data = JSON.parse(e.data) as { text: string; msg_id: string; i?: number };
				// const list = this.messagesMap.get(roomId);
				// if (!list) return;

				const msg = { ...this._messages.find((m) => m.id === data.msg_id) } as MessagesResponse;
				if (!msg || msg.status !== 'streaming') return;

				// const nextI = data.i ?? ((msg as any)._last_i ?? 0) + 1;
				// if ((msg as any)._last_i && nextI <= (msg as any)._last_i) return;
				// (msg as any)._last_i = nextI;

				msg.content = (msg.content || '') + data.text;
				const newMessages = this._messages.map((m) => (m.id === msg.id ? msg : m));
				this._messages = newMessages;
			});
			es.addEventListener('error', (e) => {
				console.error(e);
				es.close();
			});
			es.addEventListener('done', () => {
				es.close();
			});
		} else if (mode === 'post') {
			const res = await postApi('messages', {
				query: content,
				attempt_id: attemptId,
				item_id: itemId
			});
			console.log(res);
		}
	}

	async subscribe(quizAttemptId: string) {
		return pb!.collection('messages').subscribe(
			'*',
			(e) => {
				const message = e.record;
				switch (e.action) {
					case 'create': {
						const idx = this._messages.findIndex(
							(m) => m.content === message.content && m.status === 'onClient'
						);
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
