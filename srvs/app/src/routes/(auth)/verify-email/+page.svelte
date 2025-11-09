<script lang="ts">
	import posthog from 'posthog-js';
	import { goto } from '$app/navigation';
	import { pb } from '$lib/pb';
	import ThemeController from '$lib/features/ThemeController.svelte';
	import { userStore } from '$lib/apps/users/user.svelte';
	import SubscribeUser from '../../(user)/SubscribeUser.svelte';
	import { BadgeCheck, Mail } from 'lucide-svelte';

	const user = $derived(userStore.user);

	let resendCooldown = $state(0);
	let isResending = $state(false);
	let resendError = $state<string | null>(null);
	let showSuccessToast = $state(false);

	// Timer effect
	$effect(() => {
		if (resendCooldown <= 0) return;

		const interval = setInterval(() => {
			resendCooldown = Math.max(0, resendCooldown - 1);
		}, 1000);

		return () => clearInterval(interval);
	});

	// Check if user is verified
	$effect(() => {
		if (user?.verified) {
			const redirectUrl = sessionStorage.getItem('postLoginPath') || '/home';
			goto(redirectUrl);
		}
	});

	const handleResendVerification = async () => {
		if (!user?.email || resendCooldown > 0 || isResending) return;

		isResending = true;
		resendError = null;
		showSuccessToast = false;

		try {
			await pb!.collection('users').requestVerification(user.email);
			showSuccessToast = true;
			resendCooldown = 60;

			posthog.capture('verification_email_resent', {
				email: user.email
			});

			// Clear success toast after 3 seconds
			setTimeout(() => {
				showSuccessToast = false;
			}, 3000);
		} catch (err) {
			console.error(err);
			resendError =
				(err as any)?.message || 'Failed to resend verification email. Please try again.';
		} finally {
			isResending = false;
		}
	};

	const handleBackToSignUp = async () => {
		await goto('/sign-up');
	};
</script>

<SubscribeUser />

<div class="bg-linear-to-br from-base-100 to-base-200 flex min-h-screen flex-col px-4">
	<!-- Theme Controller - Left Side -->

	<!-- Success Toast - Top Right -->
	{#if showSuccessToast}
		<div class="toast toast-top toast-end z-50">
			<div class="alert alert-success">
				<BadgeCheck class="size-5 shrink-0" />
				<span>Verification email sent!</span>
			</div>
		</div>
	{/if}

	<!-- Main Content -->
	<div class="flex flex-1 items-center justify-center">
		<div class="w-full max-w-md space-y-6">
			<!-- Card Container -->
			<div class="card bg-base-100 p-2 shadow-xl">
				<div class="self-start">
					<ThemeController />
				</div>
				<div class="card-body space-y-4">
					<!-- Header Icon -->
					<div class="flex justify-center">
						<div class="bg-primary/10 flex h-14 w-14 items-center justify-center rounded-full">
							<Mail class="text-primary h-7 w-7" />
						</div>
					</div>

					<!-- Title -->
					<div class="space-y-2 text-center">
						<h1 class="text-2xl font-bold">Verify Your Email</h1>
						<p class="text-base-content/70 text-sm">
							We sent a link to <span class="font-semibold">{user?.email}</span>
						</p>
					</div>

					<!-- Instructions -->
					<div class="bg-info/10 space-y-2 rounded-lg p-3 text-sm">
						<p class="flex items-start gap-2">
							<span class="badge badge-info badge-sm shrink-0">1</span>
							<span>Check your inbox for our email</span>
						</p>
						<p class="flex items-start gap-2">
							<span class="badge badge-info badge-sm shrink-0">2</span>
							<span>Click the verification link</span>
						</p>
						<p class="flex items-start gap-2">
							<span class="badge badge-info badge-sm shrink-0">3</span>
							<span>You're all set!</span>
						</p>
					</div>

					<!-- Error Message -->
					{#if resendError}
						<div class="alert alert-error">
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-6 w-6 shrink-0 stroke-current"
								fill="none"
								viewBox="0 0 24 24"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M10 14l-2-2m0 0l-2-2m2 2l2-2m-2 2l-2 2m2-2l2 2"
								></path>
							</svg>
							<span class="text-sm">{resendError}</span>
						</div>
					{/if}

					<!-- Resend Button -->
					<div class="space-y-2 pt-2">
						<button
							onclick={handleResendVerification}
							disabled={resendCooldown > 0 || isResending || !user?.email}
							class="btn btn-primary w-full"
						>
							{#if isResending}
								<span class="loading loading-spinner loading-sm"></span>
								Sending…
							{:else if resendCooldown > 0}
								Resend in {resendCooldown}s
							{:else}
								Resend Email
							{/if}
						</button>

						{#if resendCooldown > 0}
							<p class="text-base-content/60 text-center text-xs">
								Wait before requesting a new email
							</p>
						{/if}
					</div>

					<!-- Divider -->
					<div class="divider my-1"></div>

					<!-- Back Button -->
					<button onclick={handleBackToSignUp} class="btn btn-outline btn-secondary btn-sm w-full">
						Back to Sign Up
					</button>
				</div>
			</div>
		</div>
	</div>
</div>
