<script lang="ts">
	import { updated } from '$app/state';
	import { RefreshCw, Zap, AlertCircle } from 'lucide-svelte';
	import { Modal, Button } from '@quizbee/ui-svelte-daisy';

	let show = $state(false);
	let isReloading = $state(false);

	$effect(() => {
		if (updated.current) {
			show = true;
		}
	});

	function handleUpdate() {
		isReloading = true;
		window.location.reload();
	}

	function handleDismiss() {
		show = false;
	}
</script>

{#if show}
	<Modal open={show} backdrop class="max-w-md">
		<div class="flex flex-col gap-6 p-2 sm:p-4">
			<!-- Header with Icon -->
			<div class="flex flex-col items-center gap-3 text-center">
				<div class="bg-primary/15 text-primary animate-pulse rounded-full p-4">
					<Zap class="size-8" />
				</div>
				<div>
					<h2 class="text-2xl font-bold">Update Available</h2>
					<p class="text-base-content/60 mt-1 text-sm">A new version of QuizBee is ready</p>
				</div>
			</div>

			<!-- Content -->
			<div class="space-y-3">
				<div class="bg-base-200/50 border-base-200 rounded-lg border p-3">
					<div class="flex items-start gap-2">
						<AlertCircle class="text-info mt-0.5 size-4 shrink-0" />
						<p class="text-base-content/70 text-xs leading-relaxed sm:text-sm">
							We've made improvements and bug fixes to enhance your experience.
						</p>
					</div>
				</div>

				<ul class="space-y-2">
					<li class="flex items-start gap-2 text-xs sm:text-sm">
						<span class="text-success mt-0.5">✓</span>
						<span class="text-base-content/70">Better performance</span>
					</li>
					<li class="flex items-start gap-2 text-xs sm:text-sm">
						<span class="text-success mt-0.5">✓</span>
						<span class="text-base-content/70">Latest features and fixes</span>
					</li>
					<li class="flex items-start gap-2 text-xs sm:text-sm">
						<span class="text-success mt-0.5">✓</span>
						<span class="text-base-content/70">Enhanced security</span>
					</li>
				</ul>
			</div>

			<!-- Action Buttons -->
			<div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
				<Button
					color="neutral"
					style="outline"
					size="md"
					onclick={handleDismiss}
					disabled={isReloading}
					class="sm:flex-1"
				>
					Later
				</Button>
				<Button
					color="primary"
					style="solid"
					size="md"
					onclick={handleUpdate}
					disabled={isReloading}
					class="sm:flex-1"
				>
					{#if isReloading}
						<RefreshCw class="size-4 animate-spin" />
						Updating...
					{:else}
						<RefreshCw class="size-4" />
						Reload page
					{/if}
				</Button>
			</div>

			<!-- Footer Note -->
			<p class="text-base-content/50 text-center text-[10px] sm:text-xs">Just reload the page!</p>
		</div>
	</Modal>
{/if}
