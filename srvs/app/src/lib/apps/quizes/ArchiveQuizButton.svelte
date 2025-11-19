<script lang="ts">
	import { Archive, ArchiveRestore, Loader2 } from 'lucide-svelte';
	import { Modal, Button } from '@quizbee/ui-svelte-daisy';
	import { pb } from '$lib/pb/client';
	import { goto } from '$app/navigation';

	interface Props {
		quizId: string;
		quizTitle: string;
		archived: boolean;
		onarchived?: () => void;
	}

	const { quizId, quizTitle, archived, onarchived }: Props = $props();

	let modalOpen = $state(false);
	let isProcessing = $state(false);

	async function toggleArchive() {
		try {
			isProcessing = true;

			const data = archived
				? { archived: false } // Restore: just unarchive, keep visibility
				: { archived: true, visibility: 'private' }; // Archive: set private

			await pb!.collection('quizes').update(quizId, data);

			modalOpen = false;
			onarchived?.();
		} catch (error) {
			console.error('Failed to update quiz archive status:', error);
		} finally {
			isProcessing = false;
		}
	}
</script>

<Button
	color={archived ? 'success' : 'error'}
	style="outline"
	square
	onclick={() => (modalOpen = true)}
>
	{#if archived}
		<ArchiveRestore size={20} />
	{:else}
		<Archive size={20} />
	{/if}
</Button>

<Modal class="max-w-md" backdrop open={modalOpen} onclose={() => (modalOpen = false)}>
	<div class="flex flex-col gap-6 pt-8">
		<div class="flex flex-col items-center gap-3 text-center">
			<div
				class={`rounded-full p-3 ${archived ? 'bg-success/20 text-success' : 'bg-error/20 text-error'}`}
			>
				{#if archived}
					<ArchiveRestore size={32} />
				{:else}
					<Archive size={32} />
				{/if}
			</div>
			<h3 class="text-xl font-bold">{archived ? 'Restore Quiz?' : 'Archive Quiz?'}</h3>
		</div>

		<div class="space-y-3">
			<p class="text-base-content/80 text-center text-sm leading-relaxed">
				Are you sure you want to {archived ? 'restore' : 'archive'} <strong>{quizTitle}</strong>?
			</p>
			<ul class="text-base-content/70 space-y-2 text-sm">
				{#if archived}
					<li class="flex items-start gap-2">
						<span class="text-success mt-0.5">•</span>
						<span>It will appear in your main list again</span>
					</li>
					<li class="flex items-start gap-2">
						<span class="text-base-content/60 mt-0.5">•</span>
						<span>Visibility settings will remain unchanged</span>
					</li>
				{:else}
					<li class="flex items-start gap-2">
						<span class="text-error mt-0.5">•</span>
						<span>Visibility will be set to <strong>Private</strong></span>
					</li>
					<li class="flex items-start gap-2">
						<span class="text-error mt-0.5">•</span>
						<span>It will be hidden from your main list by default</span>
					</li>
				{/if}
			</ul>
		</div>

		<div class="flex gap-2">
			<Button color="neutral" style="outline" onclick={() => (modalOpen = false)} class="flex-1">
				Cancel
			</Button>
			<Button
				color={archived ? 'success' : 'error'}
				style="solid"
				onclick={toggleArchive}
				disabled={isProcessing}
				class="flex-1"
			>
				{#if isProcessing}
					<Loader2 class="animate-spin" size={16} />
				{:else}
					{archived ? 'Restore Quiz' : 'Archive Quiz'}
				{/if}
			</Button>
		</div>
	</div>
</Modal>
