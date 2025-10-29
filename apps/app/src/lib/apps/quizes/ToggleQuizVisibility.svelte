<script lang="ts">
	import { Link, Search } from 'lucide-svelte';

	import { Modal, Button } from '@cogisoft/ui-svelte-daisy';

	import { pb } from '$lib/pb/client';
	import { QuizesVisibilityOptions } from '$lib/pb';

	interface Props {
		quizId: string;
		visibility: QuizesVisibilityOptions;
		onchange?: (visibility: QuizesVisibilityOptions) => void;
	}

	const { quizId, visibility, onchange }: Props = $props();

	let currentVisibility = $state<QuizesVisibilityOptions>(visibility);
	let showSearchConfirmModal = $state(false);
	let isUpdating = $state(false);

	const isSearchable = $derived(currentVisibility === QuizesVisibilityOptions.search);

	// Update visibility in backend
	async function updateVisibility(newVisibility: QuizesVisibilityOptions) {
		if (isUpdating || currentVisibility === newVisibility) return;

		try {
			isUpdating = true;
			await pb!.collection('quizes').update(quizId, {
				visibility: newVisibility
			});
			currentVisibility = newVisibility;
			onchange?.(newVisibility);
		} catch (error) {
			console.error('Failed to update visibility:', error);
			// Revert on error
			currentVisibility = visibility;
		} finally {
			isUpdating = false;
		}
	}

	// Handle search toggle (public <-> search)
	function handleSearchToggleClick(e: MouseEvent) {
		// Always prevent default to control state manually
		e.preventDefault();

		// If trying to enable search, show modal
		if (!isSearchable) {
			showSearchConfirmModal = true;
		} else {
			// Disable search immediately
			updateVisibility(QuizesVisibilityOptions.public);
		}
	}

	// Confirm enabling search
	async function confirmEnableSearch() {
		showSearchConfirmModal = false;
		await updateVisibility(QuizesVisibilityOptions.search);
	}

	// Cancel enabling search - called when modal is closed without confirming
	function cancelEnableSearch() {
		showSearchConfirmModal = false;
	}
</script>

<div
	class="border-base-300 bg-base-100 flex items-center justify-between gap-3 rounded-lg border p-3 shadow-sm"
>
	<div class="flex flex-1 items-center gap-2.5">
		<div
			class={isSearchable
				? 'bg-primary/20 text-primary rounded-lg p-1.5'
				: 'bg-base-300 text-base-content/60 rounded-lg p-1.5'}
		>
			{#if isSearchable}
				<Search size={18} />
			{:else}
				<Link size={18} />
			{/if}
		</div>

		<div class="flex-1">
			<h4 class="text-sm font-semibold">
				{isSearchable ? 'Public' : 'Link'}
			</h4>
			<p class="text-base-content/70 text-xs">
				{isSearchable ? 'Visible in search results' : 'Shareable only via direct link'}
			</p>
		</div>
	</div>

	<input
		type="checkbox"
		class="toggle toggle-primary toggle-md"
		checked={isSearchable}
		disabled={isUpdating}
		onclick={handleSearchToggleClick}
		style="--tglbg: oklch(var(--b3));"
	/>
</div>

<!-- Confirmation Modal for enabling search -->
<Modal class="max-w-md" backdrop open={showSearchConfirmModal} onclose={cancelEnableSearch}>
	<div class="flex flex-col gap-6 pt-8">
		<div class="flex flex-col items-center gap-3 text-center">
			<div class="bg-primary/20 text-primary rounded-full p-3">
				<Search size={32} />
			</div>
			<h3 class="text-xl font-bold">Make Quiz Searchable?</h3>
		</div>

		<div class="space-y-3">
			<p class="text-base-content/80 text-sm leading-relaxed">
				Your quiz will appear in search results, helping more people discover it.
			</p>
			<ul class="text-base-content/70 space-y-2 text-sm">
				<li class="flex items-start gap-2">
					<span class="text-success mt-0.5">✓</span>
					<span>Help others find your quiz</span>
				</li>
				<li class="flex items-start gap-2">
					<span class="text-success mt-0.5">✓</span>
					<span>Reach a wider audience</span>
				</li>
				<li class="flex items-start gap-2">
					<span class="text-base-content/60 mt-0.5">•</span>
					<span>You can disable this anytime</span>
				</li>
			</ul>
		</div>

		<div class="flex gap-2">
			<Button color="neutral" style="outline" onclick={cancelEnableSearch} class="flex-1">
				Cancel
			</Button>
			<Button color="primary" style="solid" onclick={confirmEnableSearch} class="flex-1">
				Enable Search
			</Button>
		</div>
	</div>
</Modal>

<style>
	/* Improve toggle contrast on both light and dark themes */
	:global(.toggle) {
		border-width: 2px;
		border-color: currentColor;
		opacity: 0.8;
	}

	:global(.toggle:checked) {
		opacity: 1;
		border-color: transparent;
	}

	:global(.toggle:disabled) {
		opacity: 0.4;
		cursor: not-allowed;
	}

	/* Ensure toggle is visible in dark mode */
	:global([data-theme='dark'] .toggle:not(:checked)) {
		background-color: oklch(var(--b1));
		border-color: oklch(var(--bc) / 0.3);
	}
</style>
