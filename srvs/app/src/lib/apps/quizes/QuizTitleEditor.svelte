<script lang="ts">
	import type { ClassValue } from 'svelte/elements';
	import { Pencil, Save, X, Loader2 } from 'lucide-svelte';
	import { Button, Input } from '@quizbee/ui-svelte-daisy';
	import { pb } from '$lib/pb/client';

	interface Props {
		quizId: string;
		initialTitle: string;
		isOwner: boolean;
		class?: ClassValue;
	}

	const { quizId, initialTitle, isOwner, class: className }: Props = $props();

	let isEditing = $state(false);
	let title = $state(initialTitle);
	let isLoading = $state(false);

	async function saveTitle() {
		if (!title.trim() || title === initialTitle) {
			isEditing = false;
			title = initialTitle;
			return;
		}

		try {
			isLoading = true;
			await pb!.collection('quizes').update(quizId, {
				title: title.trim()
			});
			isEditing = false;
		} catch (error) {
			console.error('Failed to update title:', error);
			// Revert on error
			title = initialTitle;
		} finally {
			isLoading = false;
		}
	}

	function cancelEdit() {
		title = initialTitle;
		isEditing = false;
	}
</script>

{#if isOwner}
	<div class="flex items-center gap-2 {className}">
		{#if isEditing}
			<div class="flex w-full flex-1 items-center gap-2">
				<input
					bind:value={title}
					class="input input-lg w-full flex-1"
					disabled={isLoading}
					onkeydown={(e) => e.key === 'Enter' && saveTitle()}
				/>
				<Button color="primary" square onclick={saveTitle} disabled={isLoading}>
					{#if isLoading}
						<Loader2 class="animate-spin" size={14} />
					{:else}
						<Save size={14} />
					{/if}
				</Button>
				<Button square style="ghost" onclick={cancelEdit} disabled={isLoading}>
					<X size={14} />
				</Button>
			</div>
		{:else}
			<h1 class="group flex items-center gap-2 text-3xl font-bold leading-tight">
				{title}
				<Button
					size="sm"
					square
					style="outline"
					color="neutral"
					class="transition-opacity group-hover:opacity-100"
					onclick={() => (isEditing = true)}
				>
					<Pencil size={18} />
				</Button>
			</h1>
		{/if}
	</div>
{:else}
	<h1 class="text-3xl font-bold leading-tight">{title}</h1>
{/if}
