<script lang="ts">
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte.js';
	import { materialsStore } from '$lib/apps/materials/materials.svelte.js';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte.js';

	import Button from '$lib/ui/Button.svelte';
	import { computeApiUrl } from '$lib/api/compute-url';
	import Input from '$lib/ui/Input.svelte';
	import { goto } from '$app/navigation';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import { pb, type MaterialsResponse } from '$lib/pb';
	import { userStore } from '$lib/apps/users/user.svelte.js';

	const materials = $derived(materialsStore.materials);

	let query = $state('');
	let files: FileList | null = $state(null);

	let selectedMaterials: MaterialsResponse[] = $state([]);

	let loading = $state(false);

	async function send() {
		loading = true;
		const payload = {
			query,
			material_ids: selectedMaterials.map((m) => m.id),
			with_attempt: true
		};

		const r1 = await fetch(`${computeApiUrl()}/quizes`, {
			method: 'POST',
			body: JSON.stringify(payload),
			headers: {
				'Content-Type': 'application/json'
			},
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

		uiStore.setGlobalSidebarOpen(false);
		await goto(`/quizes/${quizId}/attempts/${quizAttemptsId}`);
		loading = false;
	}
</script>

<div>
	<Input type="text" bind:value={query} />
	<Button onclick={send} disabled={loading}>Test Quiz</Button>

	<input
		onchange={async (e) => {
			const input = e.target as HTMLInputElement | null;
			const newFiles = input?.files || [];
			if (!newFiles) return;

			for (const m of selectedMaterials) {
				try {
					await pb!.collection('materials').delete(m.id);
					selectedMaterials = selectedMaterials.filter((m) => m.id !== m.id);
				} catch (error) {
					console.error('Failed to delete material', error);
				}
			}

			for (const file of newFiles) {
				try {
					const m = await pb!.collection('materials').create({
						file: file,
						title: file.name,
						user: userStore.user!.id
					});
					if (m) selectedMaterials.push(m);
				} catch (error) {
					console.error('Failed to create material', error);
				}
			}
		}}
		type="file"
		class="file-input"
		bind:files
	/>

	{#each selectedMaterials as material}
		<div>
			{material.file}
		</div>
	{/each}

	<p>TOTAL Materials</p>

	{#each materials as material}
		<div>
			{material.file}
		</div>
	{/each}

	<p>Files</p>

	{#each files || [] as file}
		<div>
			{file.name}
		</div>
	{/each}
</div>
