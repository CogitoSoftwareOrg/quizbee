<script lang="ts">
	import { goto, invalidate } from '$app/navigation';
	import { page } from '$app/state';

	import { pb } from '$lib/pb';

	interface Props {
		error?: any | null;
		loading?: boolean;
		disabled?: boolean;
	}

	let { error = $bindable(null), loading = $bindable(false) }: Props = $props();

	const providers = [
		{
			label: 'google',
			name: 'Google'
		}
	];

	const onClick = async (e: MouseEvent) => {
		loading = true;
		try {
			const target = e.currentTarget as HTMLElement;
			await pb!.collection('users').authWithOAuth2({
				provider: target.dataset.provider!,
				query: { expand: '', requestKey: 'oauth2' },
				createData: {
					metadata: {
						provider: target.dataset.provider!
					}
				}
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
					disabled={loading}
					data-provider={provider.label}
				>
					Sign in with {provider.name}
				</button>
			</li>
		{/each}
	</ul>
	{#if error}
		<p class="text-error mt-2 text-sm">{error.message}</p>
	{/if}
</aside>
