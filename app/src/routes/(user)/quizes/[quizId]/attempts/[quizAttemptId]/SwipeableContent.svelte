<script lang="ts">
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	interface Props {
		canSwipeLeft: boolean;
		canSwipeRight: boolean;
		onSwipeLeft: () => void;
		onSwipeRight: () => void;
		children: any;
		class?: string;
	}

	const {
		canSwipeLeft,
		canSwipeRight,
		onSwipeLeft,
		onSwipeRight,
		children,
		class: className
	}: Props = $props();

	let touchStartX = $state(0);
	let touchStartY = $state(0);
	let touchCurrentX = $state(0);
	let isDragging = $state(false);
	let isHorizontalSwipe = $state(false);
	let translateX = $state(0);
	let showInitialHint = $state(true);

	const SWIPE_THRESHOLD = 70;
	const MAX_TRANSLATE = 120;
	const DIRECTION_THRESHOLD = 10; // для определения направления свайпа
	const HINT_DURATION = 3000; // показываем анимированную подсказку 3 секунды

	// Скрываем анимированную подсказку через некоторое время
	$effect(() => {
		const timer = setTimeout(() => {
			showInitialHint = false;
		}, HINT_DURATION);
		return () => clearTimeout(timer);
	});

	function triggerHaptic() {
		// Тактильная обратная связь (если доступна)
		if ('vibrate' in navigator) {
			navigator.vibrate(10);
		}
	}

	function handleTouchStart(e: TouchEvent) {
		touchStartX = e.touches[0].clientX;
		touchStartY = e.touches[0].clientY;
		touchCurrentX = touchStartX;
		isDragging = true;
		isHorizontalSwipe = false;
		// Скрываем подсказку при первом касании
		if (showInitialHint) {
			showInitialHint = false;
		}
	}

	function handleTouchMove(e: TouchEvent) {
		if (!isDragging) return;

		const currentX = e.touches[0].clientX;
		const currentY = e.touches[0].clientY;
		const diffX = currentX - touchStartX;
		const diffY = currentY - touchStartY;

		// Определяем направление свайпа только на первом движении
		if (
			!isHorizontalSwipe &&
			(Math.abs(diffX) > DIRECTION_THRESHOLD || Math.abs(diffY) > DIRECTION_THRESHOLD)
		) {
			isHorizontalSwipe = Math.abs(diffX) > Math.abs(diffY);
			if (!isHorizontalSwipe) {
				// Это вертикальный скролл - не мешаем
				isDragging = false;
				translateX = 0;
				return;
			}
		}

		if (!isHorizontalSwipe) return;

		// Предотвращаем скролл при горизонтальном свайпе
		e.preventDefault();

		touchCurrentX = currentX;

		// Ограничиваем свайп в зависимости от доступности навигации
		if (diffX > 0 && !canSwipeLeft) {
			translateX = Math.min(diffX * 0.2, 30); // Небольшой feedback что дальше нельзя
			return;
		}
		if (diffX < 0 && !canSwipeRight) {
			translateX = Math.max(diffX * 0.2, -30);
			return;
		}

		// Применяем плавный эффект "резинки"
		let damping = 1;
		if (Math.abs(diffX) > MAX_TRANSLATE) {
			const excess = Math.abs(diffX) - MAX_TRANSLATE;
			damping = Math.max(0.1, 1 - excess / 200);
		}
		translateX = diffX * damping;
	}

	function handleTouchEnd() {
		if (!isDragging) return;

		const diff = touchCurrentX - touchStartX;

		// Проверяем, превышен ли порог для свайпа
		if (isHorizontalSwipe && Math.abs(diff) > SWIPE_THRESHOLD) {
			if (diff > 0 && canSwipeLeft) {
				triggerHaptic();
				onSwipeLeft();
			} else if (diff < 0 && canSwipeRight) {
				triggerHaptic();
				onSwipeRight();
			}
		}

		// Сброс состояния
		isDragging = false;
		isHorizontalSwipe = false;
		translateX = 0;
		touchStartX = 0;
		touchStartY = 0;
		touchCurrentX = 0;
	}

	// Индикаторы всегда видны (если доступны), но усиливаются при свайпе
	const isLeftActive = $derived(isDragging && isHorizontalSwipe && translateX > 30);
	const isRightActive = $derived(isDragging && isHorizontalSwipe && translateX < -30);

	// Базовая opacity для статичных индикаторов, увеличивается при свайпе
	const leftIndicatorOpacity = $derived(() => {
		if (!canSwipeLeft) return 0;
		if (isLeftActive) return Math.min(0.3 + translateX / 100, 1);
		// Более заметны во время начальной подсказки
		return showInitialHint ? 0.4 : 0.2;
	});

	const rightIndicatorOpacity = $derived(() => {
		if (!canSwipeRight) return 0;
		if (isRightActive) return Math.min(0.3 + Math.abs(translateX) / 100, 1);
		// Более заметны во время начальной подсказки
		return showInitialHint ? 0.4 : 0.2;
	});
</script>

<div
	class="{className} relative overflow-hidden"
	ontouchstart={handleTouchStart}
	ontouchmove={handleTouchMove}
	ontouchend={handleTouchEnd}
	ontouchcancel={handleTouchEnd}
>
	<!-- Левый индикатор свайпа -->
	{#if canSwipeLeft}
		<div
			class="bg-base-100/80 pointer-events-none absolute left-4 top-1/2 z-20 -translate-y-1/2 rounded-full p-2 shadow-lg backdrop-blur-sm transition-opacity duration-150 md:hidden"
			class:animate-pulse={showInitialHint}
			style:opacity={leftIndicatorOpacity()}
		>
			<ChevronLeft size={24} class="text-primary" />
		</div>
	{/if}

	<!-- Правый индикатор свайпа -->
	{#if canSwipeRight}
		<div
			class="bg-base-100/80 pointer-events-none absolute right-4 top-1/2 z-20 -translate-y-1/2 rounded-full p-2 shadow-lg backdrop-blur-sm transition-opacity duration-150 md:hidden"
			class:animate-pulse={showInitialHint}
			style:opacity={rightIndicatorOpacity()}
		>
			<ChevronRight size={24} class="text-primary" />
		</div>
	{/if}

	<!-- Контент с анимацией свайпа -->
	<div
		class="h-full min-w-0 overflow-x-hidden"
		style:transform={isDragging ? `translateX(${translateX}px)` : 'translateX(0)'}
		style:transition={isDragging ? 'none' : 'transform 250ms cubic-bezier(0.4, 0, 0.2, 1)'}
	>
		{@render children()}
	</div>
</div>
