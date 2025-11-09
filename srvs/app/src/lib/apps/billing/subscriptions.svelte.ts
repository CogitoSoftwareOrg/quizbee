import { pb } from '$lib/pb';
import type { SubscriptionsResponse } from '$lib/pb';

class SubscriptionStore {
	_subscription: SubscriptionsResponse | null = $state(null);

	get subscription() {
		return this._subscription;
	}
	set subscription(subscription: SubscriptionsResponse | null) {
		this._subscription = subscription;
	}

	async subscribe(subId: string) {
		return pb!.collection('subscriptions').subscribe(subId, (e) => {
			const sub = e.record;
			switch (e.action) {
				case 'update':
					this._subscription = sub;
					break;
			}
		});
	}

	unsubscribe(subId: string) {
		pb!.collection('subscriptions').unsubscribe(subId);
	}
}

export const subscriptionStore = new SubscriptionStore();
