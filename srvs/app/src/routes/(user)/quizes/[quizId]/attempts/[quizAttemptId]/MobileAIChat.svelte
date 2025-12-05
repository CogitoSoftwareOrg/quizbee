<script lang="ts">
	import { ChevronUp, X } from 'lucide-svelte';

	import { Button } from '@quizbee/ui-svelte-daisy';
	import type {
		MessagesResponse,
		QuizAttemptsResponse,
		QuizItemsResponse,
		QuizesResponse
	} from '@quizbee/pb-types';

	import type { Sender } from '$lib/apps/messages/types';
	import type { Decision } from '$lib/apps/quiz-attempts/types';

	import AIChat from './AIChat.svelte';

	interface Props {
		item: QuizItemsResponse | null;
		quizAttempt: QuizAttemptsResponse | null;
		quiz: QuizesResponse | null;
		itemDecision: Decision | null;
		messages: MessagesResponse[];
		userSender: Sender;
		assistantSender: Sender;
		open: boolean;
	}

	let {
		item,
		quizAttempt,
		quiz,
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
	let hasMoved = $state(false);
	let touchStartedOnBottom = $state(false); // отслеживаем, началось ли касание внизу экрана

	const SWIPE_THRESHOLD = 60; // Минимальное расстояние для срабатывания свайпа
	const HINT_DURATION = 4000; // Длительность анимации подсказки
	const TAP_THRESHOLD = 5; // Максимальное движение для распознавания как клика (не свайпа)
	const BOTTOM_ZONE_HEIGHT = 150; // Высота зоны внизу экрана для открытия чата
	const HANDLE_HEIGHT = 48; // Высота области для свайпа на закрытом чате

	let handleElement: HTMLElement | undefined = $state();
	let touchStartedOnHandle = $state(false); // отслеживаем, началось ли касание на handle

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
			hasMoved = false;
			touchStartedOnBottom = false;
			touchStartedOnHandle = false;
		}
	});

	// Глобальные обработчики touch событий
	$effect(() => {
		const handleTouchStart = (e: TouchEvent) => {
			// Не блокируем touch на кнопках - различаем клик от свайпа по движению (hasMoved)
			const touchY = e.touches[0].clientY;
			const windowHeight = window.innerHeight;
			const target = e.target as HTMLElement;

			if (open) {
				// Когда чат открыт - ловим только касания на handle
				const isOnHandle =
					handleElement && (target === handleElement || handleElement.contains(target));

				if (isOnHandle) {
					touchStartY = touchY;
					touchCurrentY = touchY;
					isDragging = true;
					hasMoved = false;
					touchStartedOnHandle = true;
				}
			} else if (itemDecision) {
				// Когда чат закрыт - ловим только касания в нижней зоне
				if (touchY > windowHeight - BOTTOM_ZONE_HEIGHT) {
					touchStartY = touchY;
					touchCurrentY = touchY;
					isDragging = true;
					hasMoved = false;
					touchStartedOnBottom = true;

					if (!hasInteracted) {
						hasInteracted = true;
					}
				}
			}
		};

		const handleTouchMove = (e: TouchEvent) => {
			if (!isDragging) return;

			touchCurrentY = e.touches[0].clientY;
			const diff = touchCurrentY - touchStartY;

			// Проверяем, превышен ли порог для свайпа
			if (Math.abs(diff) > TAP_THRESHOLD) {
				hasMoved = true;
			}

			// Применяем визуальные эффекты всегда, но preventDefault только при реальном свайпе
			if (open && touchStartedOnHandle) {
				// Когда открыт и касание на handle - можно только закрыть свайпом вниз
				if (diff > 0) {
					if (hasMoved) {
						e.preventDefault();
					}
					translateY = diff;
				} else {
					translateY = Math.max(diff * 0.2, -30);
				}
			} else if (touchStartedOnBottom) {
				// Когда закрыт - можно только открыть свайпом вверх из нижней зоны
				if (diff < 0) {
					if (hasMoved) {
						e.preventDefault();
					}
					const damping = Math.abs(diff) > 200 ? 0.5 : 1;
					translateY = diff * damping;
				} else {
					translateY = Math.min(diff * 0.2, 30);
				}
			}
		};

		const handleTouchEnd = () => {
			if (!isDragging) return;

			const diff = touchCurrentY - touchStartY;

			if (hasMoved) {
				if (open && touchStartedOnHandle) {
					if (diff > SWIPE_THRESHOLD) {
						open = false;
					}
				} else if (touchStartedOnBottom) {
					if (diff < -SWIPE_THRESHOLD) {
						open = true;
					}
				}
			}

			isDragging = false;
			hasMoved = false;
			translateY = 0;
			touchStartY = 0;
			touchCurrentY = 0;
			touchStartedOnBottom = false;
			touchStartedOnHandle = false;
		};

		// Добавляем глобальные обработчики
		document.addEventListener('touchstart', handleTouchStart);
		document.addEventListener('touchmove', handleTouchMove, { passive: false });
		document.addEventListener('touchend', handleTouchEnd);
		document.addEventListener('touchcancel', handleTouchEnd);

		return () => {
			document.removeEventListener('touchstart', handleTouchStart);
			document.removeEventListener('touchmove', handleTouchMove);
			document.removeEventListener('touchend', handleTouchEnd);
			document.removeEventListener('touchcancel', handleTouchEnd);
		};
	});

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

<!-- Индикатор AI чата (показывается только до первого взаимодействия) -->
{#if !open && itemDecision && !hasInteracted}
	<button
		class="bg-base-100/90 fixed bottom-4 left-1/2 z-30 -translate-x-1/2 rounded-full p-3 shadow-lg backdrop-blur-sm transition-all duration-300 hover:scale-105 active:scale-95 sm:hidden"
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

<!-- Mobile Bottom Sheet -->
<div
	class="bg-base-100 fixed inset-x-0 bottom-0 z-40 flex max-w-full flex-col overflow-hidden rounded-t-3xl shadow-2xl transition-transform duration-300 ease-out sm:hidden"
	class:pointer-events-none={!open}
	style:transform={`translateY(${chatTranslateY()})`}
	style:height="90vh"
	style:padding-top="env(safe-area-inset-top)"
	style:transition-duration={isDragging ? '0ms' : '300ms'}
>
	<div
		bind:this={handleElement}
		class="relative flex cursor-grab items-center justify-center py-3 active:cursor-grabbing"
	>
		<div class="bg-base-300 my-4 h-1.5 w-12 rounded-full"></div>
		<Button
			style="ghost"
			circle
			color="neutral"
			class="absolute right-2 top-1/2 -translate-y-1/2"
			onclick={() => (open = false)}
		>
			<X size={24} />
		</Button>
	</div>

	<!-- AIChat контент -->
	<div class="flex-1 overflow-hidden">
		<AIChat
			class="flex h-full flex-col"
			{item}
			{quizAttempt}
			{quiz}
			{itemDecision}
			{messages}
			{userSender}
			{assistantSender}
			bind:open
			showCloseButton={false}
		/>
	</div>
</div>

<!-- Overlay когда чат открыт -->
{#if open}
	<button
		class="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm transition-opacity duration-300 sm:hidden"
		onclick={() => (open = false)}
		aria-label="Close AI Chat"
	></button>
{/if}
