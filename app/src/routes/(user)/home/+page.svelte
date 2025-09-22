<script lang="ts">
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';

	import Button from '$lib/ui/Button.svelte';
	import { computeApiUrl } from '$lib/api/compute-url';
	import Input from '$lib/ui/Input.svelte';
	import { goto } from '$app/navigation';

	let query = $state('');
	let files: FileList | null = $state(null);

	async function send() {
		const data = new FormData();
		for (const file of files || []) {
			data.append('files', file);
		}
		data.append('query', query);

		const r1 = await fetch(`${computeApiUrl()}/quizes`, {
			method: 'POST',
			body: data,
			credentials: 'include'
		});
		if (!r1.ok) {
			console.error(await r1.text());
			return;
		}
		const { quiz_id: quizId, quiz_attempt_id: quizAttemptsId } = await r1.json();
		console.log(quizId, quizAttemptsId);

		const r2 = await fetch(`${computeApiUrl()}/quizes/${quizId}`, {
			method: 'PATCH',
			body: JSON.stringify({
				limit: 2
			}),
			headers: {
				'Content-Type': 'application/json'
			},
			credentials: 'include'
		});
		if (!r2.ok) {
			console.error(await r2.text());
			return;
		}
		console.log(await r2.json());

		await goto(`/quizes/${quizId}/attempts/${quizAttemptsId}`);
	}
</script>

<div>
	<Input type="text" bind:value={query} />
	<Button onclick={send}>Test Quiz</Button>

	<input type="file" class="file-input" bind:files />
</div>
