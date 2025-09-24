<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte.js';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';

	const { children } = $props();

	const quizAttemptId = $derived(page.params.quizAttemptId);
	const quizAttempt = $derived(
		quizAttemptsStore.quizAttempts.find((qa) => qa.id === quizAttemptId)
	);

	$effect(() => {
		if (userStore.loaded && !quizAttempt) goto('/home');
		if (!quizAttempt) return;

		messagesStore.load(quizAttempt.id).then(() => {
			messagesStore.subscribe(quizAttempt.id);
		});
		return () => {
			messagesStore.unsubscribe();
		};
	});
</script>

{@render children?.()}
