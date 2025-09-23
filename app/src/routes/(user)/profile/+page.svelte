<script lang="ts">
	import { z } from 'zod';
	import { Check, X, Upload, Edit } from 'lucide-svelte';

	import { pb } from '$lib/pb';
	import { userStore } from '$lib/apps/users/user.svelte';
	import Button from '$lib/ui/Button.svelte';
	import { goto } from '$app/navigation';

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

	// Edit state
	let nameValue = $derived(user?.name || '');
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

	function logout() {
		pb!.authStore.clear();
		goto('/sign-in');
	}
</script>

<div class="card bg-base-100 mx-auto max-w-2xl shadow-lg">
	<div class="card-body">
		<!-- Avatar Section -->
		<div class="mb-6 flex justify-center">
			<div class="avatar relative">
				<div
					class="ring-primary ring-offset-base-100 h-32 w-32 overflow-hidden rounded-full ring ring-offset-2"
				>
					{#if avatar}
						<img src={avatar} alt="Avatar" class="h-full w-full object-cover" />
					{:else}
						<div
							class="bg-base-300 text-base-content flex h-full w-full items-center justify-center text-3xl font-bold"
						>
							{getInitials(user?.name || 'U')}
						</div>
					{/if}
				</div>
				<label class="btn btn-circle btn-primary btn-sm absolute -bottom-1 -right-1 cursor-pointer">
					<Upload class="h-4 w-4" />
					<input type="file" accept="image/*" onchange={handleAvatarUpload} class="hidden" />
				</label>
			</div>
		</div>

		<!-- OAuth Provider Badge -->
		{#if isOAuthUser && oauthProvider}
			<div class="mb-4 flex justify-center">
				<div class={['badge gap-2', getProviderBadgeColor(oauthProvider)]}>
					<svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
							clip-rule="evenodd"
						></path>
					</svg>
					Connected via {oauthProvider}
				</div>
			</div>
		{/if}

		<!-- Profile Fields -->
		<div class="space-y-4">
			<!-- Name Field -->
			<div class="form-control">
				<label class="label">
					<span class="label-text font-semibold">Display Name</span>
				</label>
				{#if editingName}
					<div class="flex items-center gap-2">
						<input
							type="text"
							bind:value={nameValue}
							placeholder="Enter your name"
							class="input input-bordered h-12 flex-1 {nameError ? 'input-error' : ''}"
						/>
						<button
							onclick={saveName}
							disabled={savingName}
							class="btn btn-primary btn-sm h-12 w-12"
						>
							{#if savingName}
								<div class="loading loading-spinner loading-sm"></div>
							{:else}
								<Check class="h-4 w-4" />
							{/if}
						</button>
						<button onclick={cancelEditName} class="btn btn-ghost btn-sm h-12 w-12">
							<X class="h-4 w-4" />
						</button>
					</div>
					{#if nameError}
						<div class="text-error mt-1 text-sm">{nameError}</div>
					{/if}
				{:else}
					<div class="bg-base-200 flex h-12 items-center justify-between rounded-lg p-3">
						<span class="text-base-content">{user?.name || 'Not set'}</span>
						<button onclick={startEditName} class="btn btn-ghost btn-sm">
							<Edit class="h-4 w-4" />
						</button>
					</div>
				{/if}
			</div>

			<!-- Email Field (read-only for now) -->
			<div class="form-control">
				<label class="label">
					<span class="label-text font-semibold">Email</span>
				</label>
				<div class="bg-base-200 flex h-12 items-center justify-between rounded-lg p-3">
					<span class="text-base-content">{pb!.authStore.record?.email || 'Not set'}</span>
					{#if isOAuthUser && oauthProvider}
						<div class="badge badge-outline badge-sm">Managed by {oauthProvider}</div>
					{/if}
				</div>
			</div>
		</div>

		<div class="mt-3 space-y-2">
			<h4 class="text-center font-semibold">Manage your subscription with Stripe</h4>

			<div class="flex justify-center">
				<Button class="mx-auto" color="secondary" wide>Manage Subscription</Button>
			</div>
		</div>

		<!-- Logout Button -->
		<div class="mt-20 flex justify-center">
			<Button onclick={logout} color="error" style="soft" wide>Logout</Button>
		</div>
	</div>
</div>
