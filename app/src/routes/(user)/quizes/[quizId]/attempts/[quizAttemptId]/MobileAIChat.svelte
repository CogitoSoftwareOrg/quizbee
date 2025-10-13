<script lang="ts">
	import { ChevronDown, ChevronUp } from 'lucide-svelte';
	import type { Sender } from '$lib/apps/messages/types';
	import type { MessagesResponse, QuizAttemptsResponse, QuizItemsResponse } from '$lib/pb';
	import type { Decision } from '$lib/apps/quiz-attempts/types';
	import AIChat from './AIChat.svelte';

	interface Props {
		item: QuizItemsResponse | null;
		quizAttempt: QuizAttemptsResponse | null;
		itemDecision: Decision | null;
		messages: MessagesResponse[];
		userSender: Sender;
		assistantSender: Sender;
		open: boolean;
	}

	let {
		item,
		quizAttempt,
		itemDecision,
		messages,
		userSender,
		assistantSender,
		open = $bindable(false)
	}: Props = $props();

	let touchStartY = $state(0);
	let touchCurrentY = $state(0);
	let isDragging = $state(false);
	let translateY = $state(0);
	let hasInteracted = $state(false);

	const SWIPE_THRESHOLD = 60;
	const HINT_DURATION = 4000;

	// Показываем анимацию только первые 4 секунды И если не было взаимодействия
	let showPulse = $state(true);
	$effect(() => {
		const timer = setTimeout(() => {
			showPulse = false;
		}, HINT_DURATION);
		return () => clearTimeout(timer);
	});

	// Сбрасываем подсказку при закрытии чата
	$effect(() => {
		if (!open) {
			translateY = 0;
			isDragging = false;
		}
	});

	function handleTouchStart(e: TouchEvent) {
		// Проверяем, не началось ли touch на интерактивном элементе (кнопке, инпуте и т.д.)
		const target = e.target as HTMLElement;
		if (target.closest('button, a, input, textarea, select')) {
			// Если touch на интерактивном элементе, не обрабатываем его как свайп
			return;
		}

		// Предотвращаем конфликт с другими обработчиками
		e.stopPropagation();
		touchStartY = e.touches[0].clientY;
		touchCurrentY = touchStartY;
		isDragging = true;

		// Скрываем подсказку навсегда после первого взаимодействия
		if (!hasInteracted) {
			hasInteracted = true;
		}
	}

	function handleTouchMove(e: TouchEvent) {
		if (!isDragging) return;

		touchCurrentY = e.touches[0].clientY;
		const diff = touchCurrentY - touchStartY;

		if (open) {
			// Когда открыт - можно только закрыть свайпом вниз
			if (diff > 0) {
				// Свайп вниз - закрытие
				e.preventDefault();
				translateY = diff;
			} else {
				// Свайп вверх - небольшой bounce эффект
				translateY = Math.max(diff * 0.2, -30);
			}
		} else {
			// Когда закрыт - можно только открыть свайпом вверх
			if (diff < 0) {
				// Свайп вверх - открытие
				e.preventDefault();
				const damping = Math.abs(diff) > 200 ? 0.5 : 1;
				translateY = diff * damping;
			} else {
				// Свайп вниз - небольшой bounce эффект
				translateY = Math.min(diff * 0.2, 30);
			}
		}
	}

	function handleTouchEnd() {
		if (!isDragging) return;

		const diff = touchCurrentY - touchStartY;

		if (open) {
			// Закрываем если свайп вниз превышает порог
			if (diff > SWIPE_THRESHOLD) {
				open = false;
			}
		} else {
			// Открываем если свайп вверх превышает порог
			if (diff < -SWIPE_THRESHOLD) {
				open = true;
			}
		}

		// Сброс состояния
		isDragging = false;
		translateY = 0;
		touchStartY = 0;
		touchCurrentY = 0;
	}

	const hintOpacity = $derived(() => {
		if (!itemDecision) return 0;
		if (open) return 0;
		if (hasInteracted) return 0; // Скрыто после первого взаимодействия
		return showPulse ? 0.7 : 0.3; // Яркая анимация первые 4 сек, потом тусклее
	});

	const chatTranslateY = $derived(() => {
		if (!open) return '100%';
		if (isDragging) return `${translateY}px`;
		return '0';
	});
</script>

<!-- Постоянная зона свайпа внизу (всегда активна на мобилке) -->
{#if !open && itemDecision}
	<div
		class="fixed inset-x-0 bottom-0 z-30 h-24 max-w-full sm:hidden"
		ontouchstart={handleTouchStart}
		ontouchmove={handleTouchMove}
		ontouchend={handleTouchEnd}
		ontouchcancel={handleTouchEnd}
	>
		<!-- Видимый индикатор (показывается только до первого взаимодействия) -->
		{#if !hasInteracted}
			<button
				class="bg-base-100/90 absolute bottom-4 left-1/2 -translate-x-1/2 rounded-full p-3 shadow-lg backdrop-blur-sm transition-all duration-300 hover:scale-105 active:scale-95"
				class:animate-bounce={showPulse}
				style:opacity={hintOpacity()}
				onclick={() => {
					open = true;
					hasInteracted = true;
				}}
				aria-label="Open AI Chat"
			>
				<div class="flex flex-col items-center gap-1">
					<ChevronUp size={20} class="text-primary" />
					<span class="text-primary text-xs font-semibold">AI Chat</span>
				</div>
			</button>
		{/if}
	</div>
{/if}

<!-- Mobile Bottom Sheet -->
<div
	class="bg-base-100 fixed inset-x-0 bottom-0 z-40 flex max-w-full flex-col overflow-hidden rounded-t-3xl shadow-2xl transition-transform duration-300 ease-out sm:hidden"
	class:pointer-events-none={!open}
	style:transform={`translateY(${chatTranslateY()})`}
	style:height="95vh"
	style:transition-duration={isDragging ? '0ms' : '300ms'}
>
	<!-- Handle для свайпа -->
	<div
		class="flex cursor-grab items-center justify-center py-3 active:cursor-grabbing"
		ontouchstart={handleTouchStart}
		ontouchmove={handleTouchMove}
		ontouchend={handleTouchEnd}
		ontouchcancel={handleTouchEnd}
	>
		<div class="bg-base-300 h-1.5 w-12 rounded-full"></div>
	</div>

	<!-- AIChat контент -->
	<div class="flex-1 overflow-hidden">
		<AIChat
			class="flex h-full flex-col"
			{item}
			{quizAttempt}
			{itemDecision}
			{messages}
			{userSender}
			{assistantSender}
			bind:open
		/>
	</div>
</div>

<!-- Overlay когда чат открыт -->
{#if open}
	<button
		class="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm transition-opacity duration-300 sm:hidden"
		onclick={() => (open = false)}
		ontouchstart={(e) => {
			e.preventDefault();
			open = false;
		}}
		aria-label="Close AI Chat"
	></button>
{/if}
