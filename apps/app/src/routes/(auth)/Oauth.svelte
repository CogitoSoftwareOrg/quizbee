<script lang="ts">
	import posthog from 'posthog-js';
	import { goto, invalidate } from '$app/navigation';
	import { page } from '$app/state';
	import { env } from '$env/dynamic/public';

	import { pb } from '$lib/pb';

	interface Props {
		error?: any | null;
		loading?: boolean;
		agreed?: boolean;
	}

	let {
		error = $bindable(null),
		loading = $bindable(false),
		agreed = $bindable(true)
	}: Props = $props();

	const providers = [
		{
			label: 'google',
			name: 'Google'
		}
	];

	const onClick = async (e: MouseEvent) => {
		loading = false;
		try {
			const target = e.currentTarget as HTMLElement;
			posthog.capture('oauth_started', {
				provider: target.dataset.provider!
			});

			const res = await pb!.collection('users').authWithOAuth2({
				provider: target.dataset.provider!,
				query: { expand: '', requestKey: 'oauth2' },
				createData: {
					metadata: {
						provider: target.dataset.provider!
					}
				}
			});

			posthog.capture('oauth_completed', {
				provider: target.dataset.provider!
			});
			const redirectUrl = sessionStorage.getItem('postLoginPath') || '/home';
			// await invalidate('global:user');
			await goto(redirectUrl);
		} catch (e) {
			console.error('Error during OAuth2 flow:', e);
		} finally {
			loading = false;
		}
	};
</script>

<aside class="mb-4">
	<ul class="grid grid-cols-1 gap-2">
		{#each providers as provider}
			<li>
				<button
					type="button"
					class="btn btn-outline btn-block"
					onclick={onClick}
					disabled={loading || !agreed}
					data-provider={provider.label}
				>
					Sign in with {provider.name}
				</button>
			</li>
		{/each}
	</ul>
	{#if agreed}
		<p class="text-neutral mt-2 text-sm">
			By signing in with, you agree to the <a
				href={`${env.PUBLIC_WEB_URL}legal/terms-and-conditions`}
				class="link link-primary">terms and conditions</a
			>
			and
			<a href={`${env.PUBLIC_WEB_URL}legal/privacy-policy`} class="link link-primary"
				>privacy policy</a
			>.
		</p>
	{:else if !agreed}
		<p class="text-warning mt-2 text-sm">
			You must agree to the terms and conditions to sign in with
		</p>
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
	{/if}
	{#if error}
		<p class="text-error mt-2 text-sm">{error.message}</p>
	{/if}
</aside>
