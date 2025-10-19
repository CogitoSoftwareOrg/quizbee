<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	const status = $derived(page.status);

	const errorMessage = $derived(
		(() => {
			switch (status) {
				case 404:
					return {
						title: 'Page Not Found',
						description: "Sorry, the page you're looking for doesn't exist or may have been moved.",
						emoji: '🐝'
					};
				case 403:
					return {
						title: 'Access Denied',
						description:
							"You don't have permission to access this page. Please check your credentials.",
						emoji: '🔒'
					};
				case 500:
					return {
						title: 'Server Error',
						description: 'Something went wrong on our end. Please try again later.',
						emoji: '⚠️'
					};
				default:
					return {
						title: 'Something Went Wrong',
						description: page.error?.message || 'An unexpected error occurred.',
						emoji: '❌'
					};
			}
		})()
	);

	function handleGoBack() {
		if (window.history.length > 1) {
			window.history.back();
		} else {
			goto('/');
		}
	}

	function handleGoHome() {
		goto('/');
	}
</script>

<div class="bg-base-200 flex min-h-screen items-center justify-center px-4 py-8">
	<div class="flex w-full max-w-2xl items-center justify-center">
		<div class="card bg-base-100 w-full shadow-2xl">
			<div class="card-body items-center justify-center px-8 py-16 text-center">
				<!-- Error Code with Animation -->
				<div class="relative mb-8">
					<div class="text-primary select-none text-9xl font-bold opacity-20">
						{page.status}
					</div>
					<div class="absolute inset-0 flex items-center justify-center">
						<div class="animate-bounce text-7xl">
							{errorMessage.emoji}
						</div>
					</div>
				</div>

				<!-- Error Title -->
				<h1 class="card-title text-base-content mb-4 text-4xl font-bold">
					{errorMessage.title}
				</h1>

				<!-- Error Description -->
				<p class="text-base-content/70 mb-8 max-w-md text-lg">
					{errorMessage.description}
				</p>

				<!-- Action Buttons -->
				<div class="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
					<button onclick={handleGoBack} class="btn btn-outline btn-lg">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M10 19l-7-7m0 0l7-7m-7 7h18"
							/>
						</svg>
						Go Back
					</button>
					<button onclick={handleGoHome} class="btn btn-primary btn-lg">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
							/>
						</svg>
						Go Home
					</button>
				</div>

				<!-- Helpful Links -->
				{#if page.status === 404}
					<div class="border-base-300 mt-12 w-full border-t pt-8">
						<p class="text-base-content/50 mb-4 text-sm">Popular Pages</p>
						<div class="flex flex-wrap justify-center gap-2">
							<a href="/home" class="link link-hover text-sm">Home</a>
							<span class="text-base-content/30">•</span>
							<a href="/quizes" class="link link-hover text-sm">Quizzes</a>
							<span class="text-base-content/30">•</span>
							<a href="/profile" class="link link-hover text-sm">Profile</a>
							<span class="text-base-content/30">•</span>
							<a href="/analytics" class="link link-hover text-sm">Analytics</a>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	@keyframes bounce {
		0%,
		100% {
			transform: translateY(0);
		}
		50% {
			transform: translateY(-20px);
		}
	}

	.animate-bounce {
		animation: bounce 2s ease-in-out infinite;
	}
</style>
