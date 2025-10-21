<script lang="ts">
	import { Globe, Lock, Search, AlertCircle, Crown } from 'lucide-svelte';

	import { Modal, Button } from '@cogisoft/ui-svelte-daisy';

	import { pb } from '$lib/pb/client';
	import { QuizesVisibilityOptions } from '$lib/pb/pocketbase-types';
	import { uiStore } from '$lib/apps/users/ui.svelte';

	interface Props {
		quizId: string;
		visibility: QuizesVisibilityOptions;
		onchange?: (visibility: QuizesVisibilityOptions) => void;
	}

	const { quizId, visibility, onchange }: Props = $props();

	let currentVisibility = $state<QuizesVisibilityOptions>(visibility);
	let showSearchConfirmModal = $state(false);
	let isUpdating = $state(false);

	// Derived states
	const isPublic = $derived(
		currentVisibility === QuizesVisibilityOptions.public ||
			currentVisibility === QuizesVisibilityOptions.search
	);
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

	// Handle main toggle (private <-> public/search)
	async function handleMainToggle(checked: boolean) {
		if (checked) {
			// Enable public
			await updateVisibility(QuizesVisibilityOptions.public);
		} else {
			// Disable (back to private)
			await updateVisibility(QuizesVisibilityOptions.private);
		}
	}

	// Handle search toggle (public <-> search)
	function handleSearchToggleClick(e: MouseEvent) {
		const target = e.target as HTMLInputElement;

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

<div class="flex flex-col gap-3">
	<!-- Paid User: Show full toggle controls -->
	<!-- Main Toggle: Private <-> Public -->
	<div
		class="border-base-300 bg-base-100 flex items-center justify-between gap-3 rounded-lg border p-3 shadow-sm"
	>
		<div class="flex flex-1 items-center gap-2.5">
			{#if isPublic}
				<div class="bg-success/10 text-success rounded-lg p-1.5">
					<Globe size={18} />
				</div>
			{:else}
				<div class="bg-base-300 text-base-content/60 rounded-lg p-1.5">
					<Lock size={18} />
				</div>
			{/if}

			<div class="flex-1">
				<div class="flex items-center gap-2">
					<h4 class="text-sm font-semibold">
						{isPublic ? 'Public' : 'Private'}
					</h4>
					{#if currentVisibility === QuizesVisibilityOptions.search}
						<span class="badge badge-primary badge-xs">Searchable</span>
					{/if}
				</div>
				<p class="text-base-content/70 text-xs">
					{isPublic ? 'Anyone with the link can access' : 'Only you can access'}
				</p>
			</div>
		</div>

		<input
			type="checkbox"
			class="toggle toggle-success toggle-md"
			checked={isPublic}
			disabled={isUpdating}
			onchange={(e) => handleMainToggle(e.currentTarget.checked)}
			style="--tglbg: oklch(var(--b3));"
		/>
	</div>

	<!-- Search Toggle: Public <-> Search (only visible when public) -->
	{#if isPublic}
		<div
			class="border-primary/20 bg-primary/5 flex items-center justify-between gap-3 rounded-lg border p-3 shadow-sm transition-all"
		>
			<div class="flex flex-1 items-center gap-2.5">
				<div
					class={isSearchable
						? 'bg-primary/20 text-primary rounded-lg p-1.5'
						: 'bg-base-300 text-base-content/60 rounded-lg p-1.5'}
				>
					<Search size={18} />
				</div>

				<div class="flex-1">
					<h4 class="text-sm font-semibold">Make Searchable</h4>
					<p class="text-base-content/70 text-xs">
						{isSearchable ? 'Appears in search results' : 'Direct link only'}
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
	{/if}
</div>

<!-- Confirmation Modal for enabling search -->
<Modal class="max-w-md" backdrop open={showSearchConfirmModal} onclose={cancelEnableSearch}>
	<div class="flex flex-col gap-6 pt-8">
		<div class="flex flex-col items-center gap-3 text-center">
			<div class="bg-warning/20 text-warning rounded-full p-3">
				<AlertCircle size={32} />
			</div>
			<h3 class="text-xl font-bold">Make Quiz Searchable?</h3>
		</div>

		<div class="space-y-3">
			<p class="text-base-content/80 text-sm leading-relaxed">
				Enabling search will make your quiz discoverable by other users in search results. This
				means:
			</p>
			<ul class="text-base-content/70 space-y-2 text-sm">
				<li class="flex items-start gap-2">
					<span class="text-success mt-0.5">✓</span>
					<span>More people can find and take your quiz</span>
				</li>
				<li class="flex items-start gap-2">
					<span class="text-success mt-0.5">✓</span>
					<span>Your quiz will appear in relevant searches</span>
				</li>
				<li class="flex items-start gap-2">
					<span class="text-warning mt-0.5">⚠</span>
					<span>Anyone can discover it without the direct link</span>
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
