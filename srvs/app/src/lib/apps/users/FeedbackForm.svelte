<script lang="ts">
	import { Send, MessageSquare, Bug, Lightbulb } from 'lucide-svelte';

	import { Button, TextArea } from '@quizbee/ui-svelte-daisy';

	import { pb } from '$lib/pb';

	import { uiStore } from './ui.svelte';
	import { userStore } from './user.svelte';

	const user = $derived(userStore.user);

	let type = $state<'support' | 'feature'>('feature');
	let content = $state('');
	let isSubmitting = $state(false);
	let successMessage = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!content.trim() || isSubmitting) return;

		isSubmitting = true;
		successMessage = false;

		try {
			await pb!.collection('feedbacks').create({
				type,
				content: content.trim(),
				user: user?.id
			});

			// Reset form
			content = '';
			successMessage = true;

			// Close modal after 2 seconds
			setTimeout(() => {
				uiStore.setFeedbackModalOpen(false);
				successMessage = false;
			}, 2000);
		} catch (error) {
			console.error('Failed to submit feedback:', error);
			alert('Failed to submit feedback. Please try again.');
		} finally {
			isSubmitting = false;
		}
	}
</script>

<div class="flex flex-col gap-8">
	<!-- Header -->
	<div class="flex items-start gap-4">
		<div class="bg-primary/10 text-primary rounded-xl p-3">
			<MessageSquare class="size-7" />
		</div>
		<div class="flex-1">
			<h2 class="text-2xl font-bold">Feedback & Support</h2>
			<p class="text-base-content/60 mt-1.5 text-sm leading-relaxed">
				Help us improve! Share your ideas or report any issues you've encountered.
			</p>
		</div>
	</div>

	<form onsubmit={handleSubmit} class="flex flex-col gap-6">
		<!-- Type Selection -->
		<fieldset class="flex flex-col gap-4">
			<legend class="text-base-content text-base font-semibold">What can we help with?</legend>
			<div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
				<label
					class={[
						'border-base-300 hover:border-primary group relative flex cursor-pointer items-start gap-3 rounded-xl border-2 p-4 transition-all',
						type === 'feature' && 'border-primary bg-primary/5'
					]}
				>
					<input
						type="radio"
						name="type"
						value="feature"
						checked={type === 'feature'}
						onchange={() => (type = 'feature')}
						class="radio radio-primary radio-sm mt-0.5"
					/>
					<div class="flex-1">
						<div class="flex items-center gap-2">
							<Lightbulb class="size-5" />
							<span class="text-base-content font-semibold">Feature Request</span>
						</div>
						<p class="text-base-content/60 mt-1 text-sm">Suggest improvements or new features</p>
					</div>
				</label>

				<label
					class={[
						'border-base-300 hover:border-primary group relative flex cursor-pointer items-start gap-3 rounded-xl border-2 p-4 transition-all',
						type === 'support' && 'border-primary bg-primary/5'
					]}
				>
					<input
						type="radio"
						name="type"
						value="support"
						checked={type === 'support'}
						onchange={() => (type = 'support')}
						class="radio radio-primary radio-sm mt-0.5"
					/>
					<div class="flex-1">
						<div class="flex items-center gap-2">
							<Bug class="size-5" />
							<span class="text-base-content font-semibold">Report Issue</span>
						</div>
						<p class="text-base-content/60 mt-1 text-sm">Let us know about bugs or problems</p>
					</div>
				</label>
			</div>
		</fieldset>

		<!-- Content Input -->
		<div class="flex flex-col gap-3">
			<TextArea
				class="w-full"
				rows={10}
				grow
				bind:value={content}
				placeholder={type === 'support'
					? 'Please describe what went wrong in detail. Include steps to reproduce if possible...'
					: 'Tell us about your idea or suggestion. How would this improve your experience?'}
				required
				><label for="feedback-content" class="text-base-content text-base font-semibold">
					{type === 'support' ? 'Describe the issue' : 'Share your idea'}
				</label>
			</TextArea>
			<p class="text-base-content/50 text-xs">
				We read every message and will get back to you as soon as possible.
			</p>
		</div>

		<!-- Success Message -->
		{#if successMessage}
			<div class="alert alert-success shadow-lg">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="size-6 shrink-0 stroke-current"
					fill="none"
					viewBox="0 0 24 24"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
					/>
				</svg>
				<div>
					<h3 class="font-bold">Thank you for your feedback!</h3>
					<p class="text-sm">We'll review your message carefully.</p>
				</div>
			</div>
		{/if}

		<!-- Submit Buttons -->
		<div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
			<Button
				type="submit"
				color="primary"
				disabled={isSubmitting || !content.trim()}
				class="sm:w-auto"
			>
				{#if isSubmitting}
					<span class="loading loading-spinner loading-sm"></span>
					Sending...
				{:else}
					<Send size={18} />
					Send Feedback
				{/if}
			</Button>
		</div>
	</form>
</div>
