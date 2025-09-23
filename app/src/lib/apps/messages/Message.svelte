<script lang="ts">
	import { marked } from 'marked';
	import DOMPurify from 'dompurify';
	import { DateTime } from 'luxon';
	import type { ClassValue } from 'svelte/elements';

	import Man from '$lib/assets/images/Man.jpg';
	import type { MessagesResponse } from '$lib/pb';

	import type { Sender } from './types';

	interface Props {
		class?: ClassValue;
		incoming: boolean;
		msg: MessagesResponse;
		sender: Sender;
	}

	const { msg, incoming, class: className = '', sender }: Props = $props();

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
</script>

<!-- DIVIDER HAS COMPLETELY DIFFERENT UI -->

<!-- MESSAGE BUBBLE -->
<div class={['chat-group', className]}>
	<div class={incoming ? 'chat chat-start' : 'chat chat-end'}>
		<div class="chat-image avatar">
			<div class="size-10 overflow-hidden rounded-full">
				<img alt={msg.role} src={sender?.avatar || Man} class="h-full w-full object-cover" />
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

		<div
			class={[
				'prose chat-bubble max-w-[80vw] overflow-hidden break-words rounded-lg p-2',
				'[&_code]:overflow-wrap-anywhere [&_p]:overflow-wrap-anywhere [&_code]:whitespace-pre-wrap [&_code]:break-words [&_p]:break-words [&_pre]:mx-auto [&_pre]:max-w-[95%] [&_pre]:overflow-x-hidden [&_pre]:whitespace-pre-wrap [&_pre]:break-words'
			]}
			class:chat-bubble-base-200={incoming}
			class:chat-bubble-primary={!incoming}
			aria-label="Chat message"
		>
			{@html safeHtml}
		</div>
	</div>
</div>
