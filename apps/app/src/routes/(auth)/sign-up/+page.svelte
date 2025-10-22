<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { goto, invalidate } from '$app/navigation';
	import { page } from '$app/state';

	import { pb } from '$lib/pb';
	import ThemeController from '$lib/features/ThemeController.svelte';

	import Oauth from '../Oauth.svelte';

	let username = $state('');
	let email = $state('');
	let password = $state('');
	let passwordConfirm = $state('');
	let agreed = $state(false);
	let loading = $state(false);
	let error: any | null = $state(null);

	let disabled = $derived(
		email.length === 0 ||
			password.length === 0 ||
			username.length === 0 ||
			password !== passwordConfirm ||
			!agreed
	);

	const onSubmit = async (e: SubmitEvent) => {
		e.preventDefault();
		error = null;
		loading = true;

		if (password !== passwordConfirm) {
			error = { message: 'Passwords do not match' };
			return;
		}

		try {
			await pb!.collection('users').create({
				email,
				password,
				passwordConfirm,
				name: username
			});
			await pb!.collection('users').authWithPassword(email, password, {
				expand: ''
			});
			// await invalidate('global:user');
			await goto('/verify-email');
			await pb!.collection('users').requestVerification(email);
		} catch (err) {
			console.error(err);
		} finally {
			loading = false;
		}
	};
</script>

<div class="mx-auto mt-8 max-w-lg px-4">
	<ThemeController />
	<h1 class="mb-6 text-center text-3xl font-bold">Create New Account</h1>

	<div class="mb-4">
		<Oauth bind:loading bind:error />
	</div>

	<div class="divider">OR</div>

	<form onsubmit={onSubmit} class="card bg-base-100 space-y-4 p-6 shadow-lg">
		<!-- Username -->
		<div class="form-control w-full">
			<label for="username" class="label">
				<span class="label-text">Username*</span>
			</label>
			<input
				id="username"
				type="text"
				placeholder="Your username"
				bind:value={username}
				required
				class="input input-bordered w-full"
			/>
		</div>

		<!-- Email -->
		<div class="form-control w-full">
			<label for="email" class="label">
				<span class="label-text">Email*</span>
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
				<span class="label-text">Password*</span>
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

		<!-- Confirm Password -->
		<div class="form-control w-full">
			<label for="confirmPassword" class="label">
				<span class="label-text">Confirm Password*</span>
			</label>
			<input
				id="confirmPassword"
				type="password"
				placeholder="••••••••"
				bind:value={passwordConfirm}
				required
				class="input input-bordered w-full"
			/>
		</div>

		<!-- Terms Checkbox -->
		<div class="form-control w-full">
			<label for="agree" class="label flex cursor-pointer items-center">
				<input
					id="agree"
					type="checkbox"
					bind:checked={agreed}
					class="checkbox checkbox-primary mr-2"
				/>
				<span class="label-text">
					I agree to the
					<span>
						<a
							target="_blank"
							href={`${env.PUBLIC_WEB_URL}legal/terms-and-privacy`}
							class="link link-primary">Terms and Conditions</a
						>
						&nbsp;and&nbsp;
						<a
							target="_blank"
							href={`${env.PUBLIC_WEB_URL}legal/privacy-policy`}
							class="link link-primary">Privacy Policy</a
						>
					</span>
				</span>
			</label>
		</div>

		<!-- Submit Button -->
		<div class="form-control mt-2 w-full">
			<button type="submit" class="btn btn-primary w-full" {disabled}>
				{#if loading}
					Loading…
				{:else}
					Create Account
				{/if}
			</button>
		</div>
	</form>

	<p class="mt-4 text-center text-sm">
		Already have an account?
		<a href="/sign-in" class="link link-secondary font-semibold">Sign in!</a>
	</p>
</div>
