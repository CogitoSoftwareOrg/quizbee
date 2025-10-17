<script lang="ts">
	import { onMount, untrack } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	import { userStore } from '$lib/apps/users/user.svelte.js';
	import { pb } from '$lib/pb/client.js';

	const { data } = $props();
	const quiz = $derived(data.pageQuiz);

	const user = $derived(userStore.user);

	const forceStart = $derived(page.url.searchParams.get('forceStart') === 'true');

	onMount(async () => {
		if (!forceStart || !user || !quiz) return;
		const attempt = await pb!.collection('quizAttempts').create({
			user: user.id,
			quiz: quiz.id
		});
		console.log('attempt', attempt);
		await goto(`/quizes/${quiz.id}/attempts/${attempt.id}`);
	});
</script>

<div>
	{quiz?.title}
</div>
