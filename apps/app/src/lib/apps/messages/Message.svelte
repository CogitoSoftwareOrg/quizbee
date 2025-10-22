<script lang="ts">
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import { DateTime } from 'luxon';
	import type { ClassValue } from 'svelte/elements';

	import Man from '$lib/assets/images/Man.jpg';
	import type { MessagesResponse } from '$lib/pb';

	import type { Sender } from './types';
	import { Bot } from 'lucide-svelte';

	interface Props {
		class?: ClassValue;
		incoming: boolean;
		msg: MessagesResponse;
		sender: Sender;
		showHeader?: boolean;
	}

	const { msg, incoming, class: className = '', sender, showHeader = true }: Props = $props();

	// TIME
	const utcTs = DateTime.fromFormat(msg.created || '', "yyyy-MM-dd HH:mm:ss.SSS'Z'", {
		zone: 'utc'
	});

	const localTs = utcTs.isValid ? utcTs.toLocal() : utcTs;
	const formattedTime = localTs.isValid ? localTs.toFormat('h:mm a') : '';

	const rawHtml = marked.parse(msg.content || '');
	const safeHtml = DOMPurify.sanitize(rawHtml as string, {
		ADD_ATTR: ['target', 'rel']
	});

	// Check if this is an AI message waiting for response (incoming = true means AI message)
	const isWaitingForResponse = incoming && (msg.status === 'streaming' || !msg.content || msg.content.trim() === '');
	
	// Debug
	console.log('Message Debug:', {
		role: msg.role,
		incoming,
		status: msg.status,
		content: msg.content,
		contentLength: msg.content?.length,
		isWaitingForResponse
	});
</script>

<!-- DIVIDER HAS COMPLETELY DIFFERENT UI -->

<!-- MESSAGE BUBBLE -->
<div class={['chat-group', className]}>
	<div class={incoming ? 'chat chat-start' : 'chat chat-end'}>
		{#if showHeader}
			<div class="chat-image avatar">
				<div class="size-10 overflow-hidden rounded-full">
					{#if sender.role === 'ai'}
						<Bot class="h-full w-full object-cover" />
					{:else}
						<img alt={msg.role} src={sender.avatar || Man} class="h-full w-full object-cover" />
					{/if}
				</div>
			</div>

			<div class="chat-header flex items-center space-x-2">
				<span class="text-sm font-semibold">{sender?.name || sender?.id}</span>
				{#if formattedTime}
					<time datetime={msg.created} class="text-xs opacity-50">
						{formattedTime}
					</time>
				{/if}
			</div>
		{/if}

		<div
			class={[
				'prose chat-bubble max-w-[80vw] overflow-hidden break-words rounded-lg p-2',
				'[&_code]:overflow-wrap-anywhere [&_p]:overflow-wrap-anywhere [&_code]:whitespace-pre-wrap [&_code]:break-words [&_p]:break-words [&_pre]:mx-auto [&_pre]:max-w-[95%] [&_pre]:overflow-x-hidden [&_pre]:whitespace-pre-wrap [&_pre]:break-words'
			]}
			class:chat-bubble-base-200={incoming}
			class:chat-bubble={!incoming}
			aria-label="Chat message"
		>
			{#if isWaitingForResponse}
				<div class="typing-indicator">
					<span></span>
					<span></span>
					<span></span>
				</div>
			{:else}
				{@html safeHtml}
			{/if}
		</div>
	</div>
</div>

<style>
	.typing-indicator {
		display: flex;
		align-items: center;
		gap: 4px;
		height: 20px;
		min-width: 50px;
	}

	.typing-indicator span {
		width: 8px;
		height: 8px;
		border-radius: 50%;
		background-color: currentColor;
		opacity: 0.4;
		animation: typing 1.4s infinite;
	}

	.typing-indicator span:nth-child(1) {
		animation-delay: 0s;
	}

	.typing-indicator span:nth-child(2) {
		animation-delay: 0.2s;
	}

	.typing-indicator span:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes typing {
		0%,
		60%,
		100% {
			opacity: 0.4;
			transform: translateY(0);
		}
		30% {
			opacity: 1;
			transform: translateY(-10px);
		}
	}
</style>
