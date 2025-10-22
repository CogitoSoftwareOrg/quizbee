<script>
	import { goto } from '$app/navigation';

	import ThemeController from '$lib/features/ThemeController.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';

	import SubscribeUser from '../../(user)/SubscribeUser.svelte';

	const user = $derived(userStore.user);

	$effect(() => {
		console.log(user);
		if (user?.verified) {
			const redirectUrl = sessionStorage.getItem('postLoginPath') || '/home';
			goto(redirectUrl);
		}
	});
</script>

<SubscribeUser />

<div class="mx-auto mt-8 max-w-md px-4">
	<ThemeController />
	<h1 class="mb-6 text-center text-3xl font-bold">Verify Your Email</h1>
	<p class="text-center text-lg">
		We've sent a verification email to {user?.email}. Please check your inbox and click the link to
		verify your email.
	</p>
</div>
