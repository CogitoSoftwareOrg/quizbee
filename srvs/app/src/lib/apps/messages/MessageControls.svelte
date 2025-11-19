<script lang="ts">
	import { Send } from 'lucide-svelte';
	import type { ClassValue } from 'svelte/elements';

	import { Button } from '@quizbee/ui-svelte-daisy';
	import type { MessagesResponse } from '$lib/pb';

	interface Props {
		messages: MessagesResponse[];
		disabled?: boolean;
		class?: ClassValue;
		onSend: (content: string) => void | Promise<void>;
	}

	const { messages, disabled = false, class: className, onSend }: Props = $props();

	let content = $state('');
	let isSending = $state(false);
	let textareaElement: HTMLTextAreaElement | undefined = $state();

	// Constants for autogrow behavior
	const MIN_HEIGHT = 48; // ~2 lines
	const MAX_HEIGHT = 192; // ~8 lines

	const canSend = $derived.by(() => {
		if (!content.trim()) return false;
		if (isSending) return false;

		if (messages.length === 0) return true;
		const lastMessage = messages[messages.length - 1];
		return lastMessage.role === 'ai' && lastMessage.status === 'final';
	});

	// Auto-resize textarea based on content
	function adjustTextareaHeight() {
		if (!textareaElement) return;

		// Reset height to auto to get accurate scrollHeight
		textareaElement.style.height = 'auto';

		// Calculate new height based on scrollHeight
		const scrollHeight = textareaElement.scrollHeight;
		const newHeight = Math.min(Math.max(scrollHeight, MIN_HEIGHT), MAX_HEIGHT);

		textareaElement.style.height = `${newHeight}px`;

		// Enable scrolling if content exceeds max height
		textareaElement.style.overflowY = scrollHeight > MAX_HEIGHT ? 'auto' : 'hidden';
	}

	// Adjust height when content changes
	$effect(() => {
		if (content !== undefined) {
			// Use requestAnimationFrame to ensure DOM is updated
			requestAnimationFrame(() => {
				adjustTextareaHeight();
			});
		}
	});

	// Adjust height on input (for paste, etc.)
	function handleInput() {
		adjustTextareaHeight();
	}

	async function handleSend() {
		if (!canSend) return;

		isSending = true;
		try {
			await onSend(content.trim());
			content = '';
			// Reset height after sending
			if (textareaElement) {
				textareaElement.style.height = `${MIN_HEIGHT}px`;
			}
		} catch (error) {
			console.error('Failed to send message:', error);
		} finally {
			isSending = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}
</script>

<div class={['flex items-end gap-2', className]}>
	<textarea
		bind:this={textareaElement}
		bind:value={content}
		onkeydown={handleKeydown}
		oninput={handleInput}
		placeholder="Type your message... (Shift+Enter for new line)"
		class="textarea-bordered textarea flex-1 resize-none"
		style="min-height: {MIN_HEIGHT}px; max-height: {MAX_HEIGHT}px;"
		rows="2"
		disabled={disabled || isSending}
	></textarea>
	<Button
		square
		onclick={handleSend}
		size="md"
		color="primary"
		disabled={disabled || !canSend}
		class="shrink-0"
	>
		{#if isSending}
			<span class="loading loading-sm loading-spinner"></span>
		{:else}
			<Send class="size-6" />
		{/if}
	</Button>
</div>
