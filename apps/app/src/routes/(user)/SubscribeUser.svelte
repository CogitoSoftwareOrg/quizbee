<script lang="ts">
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { quizItemsStore } from '$lib/apps/quizes/quizItems.svelte';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';

	const user = $derived(userStore.user);
	const sub = $derived(subscriptionStore.subscription);

	$effect(() => {
		const userId = user?.id;
		if (!userId) return;

		userStore.subscribe(userId);
		materialsStore.subscribe(userId);
		quizAttemptsStore.subscribe(userId);
		quizesStore.subscribe(userId);
		quizItemsStore.subscribe(userId);

		return () => {
			userStore.unsubscribe(userId);
			materialsStore.unsubscribe();
			quizAttemptsStore.unsubscribe();
			quizesStore.unsubscribe();
			quizItemsStore.unsubscribe();
		};
	});

	$effect(() => {
		const subId = sub?.id;
		if (!subId) return;

		subscriptionStore.subscribe(subId);

		return () => {
			subscriptionStore.unsubscribe(subId);
		};
	});
</script>
