<script lang="ts">
	import { goto } from '$app/navigation';

	import { pb } from '$lib/pb';
	import Oauth from '../Oauth.svelte';

	let email = $state('');
	let password = $state('');
	let loading = $state(false);
	let error: any | null = $state(null);

	// enable when both fields have content
	const canSubmit = $derived(email.length > 0 && password.length > 0);

	async function onSubmit(e: SubmitEvent) {
		e.preventDefault();
		error = null;
		loading = true;

		try {
			await pb!.collection('users').authWithPassword(email, password, {
				expand: ''
			});
			await goto('/');
		} catch (err) {
			console.error(err);
			error = err as any;
		} finally {
			loading = false;
		}
	}
</script>

<div class="mx-auto mt-8 max-w-md px-4">
	<h1 class="mb-6 text-center text-3xl font-bold">Sign In to Your Account</h1>

	<!-- OAuth buttons -->
	<div class="mb-4">
		<Oauth bind:loading bind:error />
	</div>

	<div class="divider">OR</div>

	<!-- Sign-in form -->
	<form onsubmit={onSubmit} class="card bg-base-100 space-y-4 p-6 shadow-lg">
		<!-- Email -->
		<div class="form-control w-full">
			<label for="email" class="label">
				<span class="label-text">Email</span>
			</label>
			<input
				id="email"
				type="email"
				placeholder="you@example.com"
				bind:value={email}
				required
				class="input input-bordered w-full"
			/>
		</div>

		<!-- Password -->
		<div class="form-control w-full">
			<label for="password" class="label">
				<span class="label-text">Password</span>
			</label>
			<input
				id="password"
				type="password"
				placeholder="••••••••"
				bind:value={password}
				required
				class="input input-bordered w-full"
			/>
		</div>

		{#if error}
			<p class="text-error text-sm">{error.message}</p>
		{/if}

		<!-- Submit -->
		<div class="form-control mt-2 w-full">
			<button type="submit" class="btn btn-primary w-full" disabled={!canSubmit || loading}>
				{#if loading}
					Signing In...
				{:else}
					Sign In
				{/if}
			</button>
		</div>
	</form>

	<p class="mt-4 text-center text-sm">
		Don’t have an account?
		<a href="/sign-up" class="link link-primary font-semibold">Create one</a>
	</p>
</div>
