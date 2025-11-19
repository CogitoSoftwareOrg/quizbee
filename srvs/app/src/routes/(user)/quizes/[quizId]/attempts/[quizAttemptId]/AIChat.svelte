<script lang="ts">
	import type { ClassValue } from 'svelte/elements';

	import { Button } from '@quizbee/ui-svelte-daisy';

	import type { Sender } from '$lib/apps/messages/types';
	import type {
		MessagesResponse,
		QuizAttemptsResponse,
		QuizItemsResponse,
		QuizesResponse
	} from '$lib/pb';

	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import Messages from '$lib/apps/messages/Messages.svelte';
	import MessageControls from '$lib/apps/messages/MessageControls.svelte';
	import { Crown, HelpCircle, X } from 'lucide-svelte';
	import { subscriptionStore } from '$lib/apps/billing/subscriptions.svelte';
	import { uiStore } from '$lib/apps/users/ui.svelte';
	import { messagesStore } from '$lib/apps/messages/stores/messages.svelte';

	interface Props {
		class?: ClassValue;
		item: QuizItemsResponse | null;
		quizAttempt: QuizAttemptsResponse | null;
		quiz: QuizesResponse | null;
		itemDecision: Decision | null;
		messages: MessagesResponse[];
		userSender: Sender;
		assistantSender: Sender;
		open: boolean;
		showCloseButton?: boolean;
	}

	let {
		class: className,
		item,
		quizAttempt,
		quiz,
		itemDecision,
		messages,
		userSender,
		assistantSender,
		open = $bindable(false),
		showCloseButton = true
	}: Props = $props();

	const sub = $derived(subscriptionStore.subscription);
	const isFreePlan = $derived(sub?.tariff === 'free');
	const canChat = $derived(itemDecision && item && quizAttempt && quiz);

	async function handleSend(content: string) {
		if (!item || !quizAttempt || !quiz) return;
		await messagesStore.sendMessage(userSender, content, quizAttempt.id, quiz.id, item.id);
	}
</script>

<div class={['flex h-full flex-col overflow-hidden', className]}>
	<header class="border-base-200 relative flex items-center justify-center border-b px-3 py-2">
		<h2 class="text-sm font-semibold uppercase tracking-wide">AI Chat</h2>
		{#if showCloseButton}
			<Button
				style="ghost"
				circle
				color="neutral"
				class="absolute right-3"
				onclick={() => (open = false)}
			>
				<X size={36} />
			</Button>
		{/if}
	</header>

	<section class="flex flex-1 flex-col overflow-hidden px-3 py-0">
		{#if canChat && quiz && item && quizAttempt}
			<div class="flex-1 overflow-y-auto pr-1">
				<Messages
					class="flex-1"
					{messages}
					{userSender}
					{assistantSender}
					{quiz}
					quizAttemptId={quizAttempt.id}
					itemId={item.id}
				/>
			</div>
		{:else}
			<div class="flex flex-1 items-center justify-center px-6">
				<div
					class="border-base-200 bg-base-100 flex flex-col items-center gap-3 rounded-xl border p-8 text-center shadow-sm"
				>
					<HelpCircle class="opacity-40" size={48} />
					<div class="space-y-1">
						<p class="font-medium">Answer the question first</p>
						<p class="text-base-content/70 text-sm">
							You need to answer the question before interacting with the AI
						</p>
					</div>
				</div>
			</div>
		{/if}
	</section>

	<footer class="border-base-200 border-t px-3 py-2">
		{#if isFreePlan && quiz && item && quizAttempt}
			<Button
				size="lg"
				color="neutral"
				style="soft"
				block
				onclick={() => uiStore.setPaywallOpen(true)}
				class="flex items-center justify-center gap-2"
			>
				<p class="text-center font-semibold">Only premium users can use chat with AI</p>
				<Crown class="block" size={24} />
			</Button>
		{:else if quiz && item && quizAttempt}
			<MessageControls {messages} onSend={handleSend} />
		{/if}
	</footer>
</div>
