<script lang="ts">
	import { Search, Trash2, Upload, FileText, Calendar, Database, Filter } from 'lucide-svelte';
	import { Input, Button, Modal } from '@quizbee/ui-svelte-daisy';
	import type { MaterialsResponse } from '@quizbee/pb-types';
	import type { ClassValue } from 'svelte/elements';
	import { pb } from '$lib/pb';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import { computeApiUrl } from '$lib/api/compute-url';
	import { deleteApi } from '$lib/api/call-api';
	import { generateId } from '$lib/utils/generate-id';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';

	interface Props {
		class?: ClassValue;
		materials: MaterialsResponse[];
		userId: string;
	}

	const { class: className = '', materials, userId }: Props = $props();

	// Filter state
	let searchQuery = $state('');
	let selectedStatuses = $state<string[]>([]);
	let showFilters = $state(false);
	let showDeleteModal = $state(false);
	let materialToDelete = $state<MaterialsResponse | null>(null);
	let isDeleting = $state(false);

	// File upload state
	let fileInputElement = $state<HTMLInputElement>();
	let isUploading = $state(false);

	// Get storage info from subscription
	const subscription = $derived(subscriptionStore.subscription);
	const storageUsage = $derived(subscription?.storageUsage ?? 0);
	const storageLimit = $derived(subscription?.storageLimit ?? 0);
	const storageProgress = $derived(storageLimit > 0 ? (storageUsage / storageLimit) * 100 : 0);

	const filteredMaterials = $derived.by(() => {
		const search = searchQuery.trim().toLowerCase();
		let result = materials;

		// Search filter
		if (search) {
			result = result.filter((item) => {
				if (item.title.toLowerCase().includes(search)) return true;
				return false;
			});
		}

		// Status filter
		if (selectedStatuses.length > 0) {
			result = result.filter((item) => selectedStatuses.includes(item.status || ''));
		}

		return result.toSorted((a, b) => b.created.localeCompare(a.created));
	});

	function formatDateTime(value: string): string {
		if (!value) return '';
		try {
			return new Intl.DateTimeFormat(undefined, {
				dateStyle: 'medium',
				timeStyle: 'short'
			}).format(new Date(value));
		} catch (error) {
			return value;
		}
	}

	function formatBytes(bytes: number): string {
		if (bytes === 0) return '0 B';
		const k = 1024;
		const sizes = ['B', 'KB', 'MB', 'GB'];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
	}

	function toggleStatus(status: string) {
		if (selectedStatuses.includes(status)) {
			selectedStatuses = selectedStatuses.filter((s) => s !== status);
		} else {
			selectedStatuses = [...selectedStatuses, status];
		}
	}

	function resetFilters() {
		searchQuery = '';
		selectedStatuses = [];
	}

	const hasActiveFilters = $derived(searchQuery || selectedStatuses.length > 0);

	function openDeleteModal(material: MaterialsResponse) {
		materialToDelete = material;
		showDeleteModal = true;
	}

	function closeDeleteModal() {
		showDeleteModal = false;
		materialToDelete = null;
	}

	async function confirmDelete() {
		if (!materialToDelete) return;

		isDeleting = true;
		try {
			// Use the backend API to delete material (automatically updates storage)
			await deleteApi(`materials/${materialToDelete.id}`);
			closeDeleteModal();
		} catch (error) {
			console.error('Failed to delete material:', error);
		} finally {
			isDeleting = false;
		}
	}

	function openFileUpload() {
		fileInputElement?.click();
	}

	async function handleFileUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		const files = target.files;
		if (!files || files.length === 0) return;

		isUploading = true;
		const allowedExtensions = ['pdf', 'pptx', 'docx', 'md', 'txt', 'html', 'xlsx', 'csv'];

		try {
			for (const file of Array.from(files)) {
				const extension = file.name.split('.').pop()?.toLowerCase();
				if (!extension || !allowedExtensions.includes(extension)) {
					console.warn('Unsupported file type:', file.name);
					continue;
				}

				// Check file size (100MB limit)
				if (file.size > 1024 * 1024 * 100) {
					console.warn('File too large:', file.name);
					continue;
				}

				const formData = new FormData();
				formData.append('file', file);
				formData.append('title', file.name);
				// Generate a unique material ID
				const materialId = generateId();
				formData.append('material_id', materialId);
				// quiz_id is now optional - not providing it for standalone materials

				// Upload using the new materials endpoint
				const response = await fetch(`${computeApiUrl()}materials`, {
					method: 'POST',
					body: formData,
					credentials: 'include'
				});

				if (!response.ok) {
					const errorText = await response.text();
					console.error('Upload failed for:', file.name, errorText);
				}
			}
		} catch (error) {
			console.error('Error uploading files:', error);
		} finally {
			isUploading = false;
			if (fileInputElement) {
				fileInputElement.value = '';
			}
		}
	}

	const statusColors: Record<string, string> = {
		indexed: 'badge-success',
		uploading: 'badge-warning',
		used: 'badge-info',
		'too big': 'badge-error',
		'no text': 'badge-error'
	};
</script>

<div class={['flex h-full flex-col gap-6 overflow-y-auto md:overflow-y-visible', className]}>
	<header class="flex shrink-0 flex-col gap-3">
		<div class="flex items-start justify-between gap-4">
			<div>
				<h1 class="text-3xl font-semibold tracking-tight">My Materials</h1>
				<p class="text-base-content/70 mt-1 text-sm">Manage your uploaded documents and files.</p>
			</div>
			<Button color="primary" style="solid" onclick={openFileUpload} disabled={isUploading}>
				<Upload size={18} />
				{isUploading ? 'Uploading...' : 'Upload Material'}
			</Button>
		</div>

		<!-- Storage Progress Widget -->
		{#if storageLimit > 0}
			<div class="bg-base-200/50 border-base-300 rounded-lg border p-4">
				<div class="mb-2 flex items-center justify-between">
					<span class="text-sm font-semibold">Storage</span>
					<span class="text-base-content/70 text-xs">
						{formatBytes(storageUsage)} / {formatBytes(storageLimit)}
					</span>
				</div>
				<progress
					class={[
						'progress',
						storageProgress >= 90
							? 'progress-error'
							: storageProgress >= 70
								? 'progress-warning'
								: 'progress-primary'
					]}
					value={storageProgress}
					max="100"
				></progress>
				<div class="mt-1 flex items-center justify-between gap-2">
					<div class="text-base-content/60 text-xs">
						{Math.round(storageProgress)}% used
					</div>
					<div class="text-base-content/60 text-xs">
						{formatBytes(storageLimit - storageUsage)} remaining
					</div>
				</div>
			</div>
		{/if}

		<div class="flex flex-col gap-3 sm:flex-row">
			<Input
				class="w-full flex-1"
				placeholder="Search by title"
				value={searchQuery}
				oninput={(event) => {
					const target = event.target as HTMLInputElement;
					searchQuery = target.value;
				}}
			>
				{#snippet children()}
					<Search class="opacity-50" size={18} />
				{/snippet}
			</Input>

			<Button
				color={showFilters || hasActiveFilters ? 'primary' : 'neutral'}
				style={showFilters || hasActiveFilters ? 'solid' : 'outline'}
				onclick={() => (showFilters = !showFilters)}
				class="sm:w-auto"
			>
				<Filter size={18} />
				Filters
				{#if hasActiveFilters && !showFilters}
					<span class="badge badge-sm">•</span>
				{/if}
			</Button>
		</div>

		{#if showFilters}
			<div class="bg-base-200/50 border-base-300 flex flex-col gap-5 rounded-xl border p-5">
				<!-- Status Filter -->
				<div class="flex flex-col gap-2">
					<span class="label-text font-medium">Status</span>
					<div class="flex flex-wrap gap-2">
						<Button
							size="sm"
							color={selectedStatuses.includes('indexed') ? 'success' : 'neutral'}
							style={selectedStatuses.includes('indexed') ? 'solid' : 'outline'}
							onclick={() => toggleStatus('indexed')}
						>
							Indexed
						</Button>
						<Button
							size="sm"
							color={selectedStatuses.includes('uploading') ? 'warning' : 'neutral'}
							style={selectedStatuses.includes('uploading') ? 'solid' : 'outline'}
							onclick={() => toggleStatus('uploading')}
						>
							Uploading
						</Button>
						<Button
							size="sm"
							color={selectedStatuses.includes('used') ? 'info' : 'neutral'}
							style={selectedStatuses.includes('used') ? 'solid' : 'outline'}
							onclick={() => toggleStatus('used')}
						>
							Used
						</Button>
					</div>
				</div>

				{#if hasActiveFilters}
					<div class="border-base-300 flex justify-end border-t pt-3">
						<Button size="sm" style="ghost" onclick={resetFilters}>Reset all filters</Button>
					</div>
				{/if}
			</div>
		{/if}
	</header>

	<section class="-ml-5 flex flex-col gap-4 md:min-h-0 md:flex-1">
		{#if filteredMaterials.length === 0}
			<div
				class="border-base-200 bg-base-100 flex flex-col items-center gap-3 rounded-xl border p-8 text-center shadow-sm"
			>
				{#if hasActiveFilters}
					<Search class="opacity-40" size={48} />
					<div>
						<p class="font-medium">No materials match your search</p>
						<p class="text-base-content/70 text-sm">
							Adjust the keywords or clear the filters to see more results.
						</p>
					</div>
					<Button size="sm" onclick={resetFilters}>Clear filters</Button>
				{:else}
					<FileText class="opacity-40" size={48} />
					<div>
						<p class="font-medium">No materials yet</p>
						<p class="text-base-content/70 text-sm">Upload your first material to get started.</p>
					</div>
					<Button size="sm" color="primary" onclick={openFileUpload}>
						<Upload size={16} />
						Upload Material
					</Button>
				{/if}
			</div>
		{:else}
			<ul class="grid gap-4 py-2 pr-1 md:overflow-y-auto">
				{#each filteredMaterials as material}
					<li>
						<div
							class="border-base-200 hover:bg-base-200/60 bg-base-100 group flex flex-col gap-4 rounded-xl border p-5 shadow-sm transition"
						>
							<div class="flex flex-wrap items-start justify-between gap-3">
								<div class="flex-1">
									<p
										class="group-hover:text-primary text-lg font-semibold leading-tight transition"
									>
										{material.title}
									</p>
									<div class="text-base-content/70 mt-2 flex items-center gap-2 text-xs">
										<Calendar size={12} class="opacity-60" />
										<span>Created: {formatDateTime(material.created)}</span>
									</div>
								</div>
								<Button color="error" style="outline" onclick={() => openDeleteModal(material)}>
									<Trash2 size={18} />
									Delete
								</Button>
							</div>

							<div class="flex flex-wrap items-center gap-2">
								{#if material.status}
									<span class={['badge', statusColors[material.status] || 'badge-ghost']}>
										{material.status.charAt(0).toUpperCase() + material.status.slice(1)}
									</span>
								{/if}

								{#if material.tokens}
									<span class="badge badge-outline">
										<Database size={12} />
										{material.tokens} tokens
									</span>
								{/if}

								{#if material.isBook}
									<span class="badge badge-accent">Book</span>
								{/if}
							</div>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</section>
</div>

<!-- Hidden file input -->
<input
	type="file"
	bind:this={fileInputElement}
	onchange={handleFileUpload}
	multiple
	accept=".pdf,.pptx,.docx,.md,.txt,.html,.xlsx,.csv"
	style="display: none;"
/>

<!-- Delete Confirmation Modal -->
<Modal class="max-w-md" backdrop open={showDeleteModal} onclose={closeDeleteModal}>
	{#snippet children()}
		<div class="flex flex-col gap-4">
			<div>
				<h3 class="text-xl font-bold">Delete Material?</h3>
				<p class="text-base-content/70 mt-2">
					Are you sure you want to delete "{materialToDelete?.title}"? This action cannot be undone.
				</p>
			</div>

			<div class="bg-warning/10 border-warning/30 rounded-lg border p-3">
				<p class="text-warning text-sm font-medium">
					⚠️ Warning: This material will be permanently removed from your account and will free up
					storage space.
				</p>
			</div>

			<div class="flex gap-2">
				<Button
					class="flex-1"
					color="neutral"
					style="outline"
					onclick={closeDeleteModal}
					disabled={isDeleting}
				>
					Cancel
				</Button>
				<Button
					class="flex-1"
					color="error"
					style="solid"
					onclick={confirmDelete}
					disabled={isDeleting}
				>
					{isDeleting ? 'Deleting...' : 'Delete'}
				</Button>
			</div>
		</div>
	{/snippet}
</Modal>
