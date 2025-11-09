<script lang="ts">
	import { z } from 'zod';
	import { Check, X, Upload, Edit } from 'lucide-svelte';
	import { pb } from '$lib/pb';
	import { userStore } from '$lib/apps/users/user.svelte';

	const user = $derived(userStore.user);
	const avatar = $derived(user?.avatar ? pb!.files.getURL(user, user.avatar) : null);

	const isOAuthUser = $derived(
		user?.metadata ? (user.metadata as any).provider || (user.metadata as any).oauth2 : false
	);

	const oauthProvider = $derived(
		user?.metadata
			? (user.metadata as any).provider || (user.metadata as any).oauth2?.provider || null
			: null
	);

	// Edit state for name
	let nameValue = $state('');
	let editingName = $state(false);
	let savingName = $state(false);
	let nameError = $state('');

	const nameSchema = z.string().min(1, 'Name is required');

	function startEditName() {
		nameValue = user?.name || '';
		nameError = '';
		editingName = true;
	}

	function cancelEditName() {
		editingName = false;
		nameError = '';
	}

	async function saveName() {
		try {
			nameSchema.parse(nameValue);
			savingName = true;
			await pb!.collection('users').update(user?.id || '', {
				id: user?.id || '',
				name: nameValue
			});
			// Optimistic local update
			if (userStore.user) userStore.user = { ...userStore.user, name: nameValue } as any;
			editingName = false;
			nameError = '';
		} catch (error) {
			if (error instanceof z.ZodError) {
				nameError = error.issues[0].message;
			} else {
				nameError = 'Failed to update name';
			}
		} finally {
			savingName = false;
		}
	}

	// Avatar upload
	async function handleAvatarUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		if (!target.files || !target.files[0]) return;
		const file = target.files[0];
		try {
			await pb!.collection('users').update(user?.id || '', {
				id: user?.id || '',
				avatar: file
			});
		} catch (err) {
			console.error('Failed to update avatar', err);
		}
	}

	function getInitials(name: string): string {
		return name
			.split(' ')
			.map((w) => w.charAt(0))
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}

	function getProviderBadgeColor(provider: string): string {
		switch (provider?.toLowerCase()) {
			case 'google':
				return 'badge-primary';
			case 'github':
				return 'badge-neutral';
			case 'facebook':
				return 'badge-info';
			case 'twitter':
				return 'badge-secondary';
			default:
				return 'badge-accent';
		}
	}
</script>

<div class="card bg-base-100 shadow-sm">
	<div class="card-body">
		<!-- Avatar Section -->
		<div class="mb-4 flex flex-col items-center gap-3">
			<div class="avatar relative">
				<div
					class="ring-primary ring-offset-base-100 size-24 overflow-hidden rounded-full ring-2 ring-offset-2 sm:size-28"
				>
					{#if avatar}
						<img src={avatar} alt="Avatar" class="h-full w-full object-cover" />
					{:else}
						<div
							class="bg-base-300 text-base-content flex h-full w-full items-center justify-center text-2xl font-bold sm:text-3xl"
						>
							{getInitials(user?.name || 'U')}
						</div>
					{/if}
				</div>
				<label class="btn btn-circle btn-primary btn-sm absolute -bottom-1 -right-1 cursor-pointer">
					<Upload class="h-3.5 w-3.5" />
					<input type="file" accept="image/*" onchange={handleAvatarUpload} class="hidden" />
				</label>
			</div>

			<!-- OAuth Badge -->
			{#if isOAuthUser && oauthProvider}
				<div class={['badge badge-sm gap-1.5', getProviderBadgeColor(oauthProvider)]}>
					<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						></path>
					</svg>
					{oauthProvider}
				</div>
			{/if}
		</div>

		<!-- Name Field -->
		<div class="form-control">
			<div class="label">
				<span class="label-text text-xs font-semibold">Display Name</span>
			</div>
			{#if editingName}
				<div class="flex items-center gap-2">
					<input
						type="text"
						bind:value={nameValue}
						placeholder="Enter your name"
						class="input input-bordered input-sm flex-1 {nameError ? 'input-error' : ''}"
					/>
					<button
						onclick={saveName}
						disabled={savingName}
						class="btn btn-primary btn-sm btn-square"
					>
						{#if savingName}
							<div class="loading loading-spinner loading-xs"></div>
						{:else}
							<Check class="h-3.5 w-3.5" />
						{/if}
					</button>
					<button onclick={cancelEditName} class="btn btn-ghost btn-sm btn-square">
						<X class="h-3.5 w-3.5" />
					</button>
				</div>
				{#if nameError}
					<div class="text-error mt-1 text-xs">{nameError}</div>
				{/if}
			{:else}
				<div class="bg-base-200 flex items-center justify-between rounded-lg p-2.5">
					<span class="text-sm font-medium">{user?.name || 'Not set'}</span>
					<button onclick={startEditName} class="btn btn-ghost btn-xs">
						<Edit class="h-3.5 w-3.5" />
					</button>
				</div>
			{/if}
		</div>

		<!-- Email Field -->
		<div class="form-control">
			<div class="label">
				<span class="label-text text-xs font-semibold">Email</span>
			</div>
			<div class="bg-base-200 flex items-center justify-between rounded-lg p-2.5">
				<span class="truncate text-sm">{pb!.authStore.record?.email || 'Not set'}</span>
				{#if isOAuthUser && oauthProvider}
					<div class="badge badge-outline badge-xs text-nowrap">OAuth</div>
				{/if}
			</div>
		</div>
	</div>
</div>
