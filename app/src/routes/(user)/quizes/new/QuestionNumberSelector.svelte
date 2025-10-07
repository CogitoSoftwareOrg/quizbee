<script lang="ts">
	let { value = $bindable(10) }: { value: number } = $props();

	const numbers = [10, 20, 30, 40, 50];

	// Преобразование значения в индекс слайдера (0-4)
	const valueToIndex = (val: number) => numbers.indexOf(val);
	const indexToValue = (idx: number) => numbers[idx];

	let sliderIndex = $state(valueToIndex(value));

	// Синхронизация значения со слайдером
	$effect(() => {
		value = indexToValue(sliderIndex);
	});

	// Вычисляем процентную позицию для заливки
	const fillPercentage = $derived((sliderIndex / (numbers.length - 1)) * 100);
</script>

<div class="mx-auto w-full max-w-xs px-4">
	<!-- Значения над слайдером -->
	<div class="relative mb-4 flex justify-between px-1">
		{#each numbers as num, i}
			<button
				type="button"
				onclick={() => (sliderIndex = i)}
				class="flex flex-col items-center transition-all duration-200"
			>
				<span
					class="text-base font-semibold transition-all duration-200 sm:text-lg {sliderIndex === i
						? 'text-warning scale-125'
						: 'text-base-content/60 hover:text-base-content/80'}"
				>
					{num}
				</span>
			</button>
		{/each}
	</div>

	<!-- Слайдер -->
	<div class="relative py-2">
		<!-- Трек слайдера -->
		<div class="bg-base-content/20 relative h-2 overflow-hidden rounded-full">
			<!-- Заливка -->
			<div
				class="bg-warning absolute left-0 top-0 h-full rounded-full transition-all duration-300"
				style="width: {fillPercentage}%"
			></div>
		</div>

		<!-- Ползунок с увеличенной областью клика -->
		<input
			type="range"
			min="0"
			max={numbers.length - 1}
			step="1"
			bind:value={sliderIndex}
			class="absolute left-0 top-0 h-full w-full cursor-pointer appearance-none bg-transparent"
			style="
				margin: 0;
				padding: 0;
			"
		/>

		<!-- Метки на треке -->
		<div
			class="pointer-events-none absolute left-0 top-1/2 flex w-full -translate-y-1/2 items-center justify-between px-0.5"
		>
			{#each numbers as _, i}
				<div
					class="bg-base-100 size-3 rounded-full border-2 transition-all duration-200 {sliderIndex ===
					i
						? 'border-warning scale-150 shadow-lg'
						: 'border-base-content/30'}"
				></div>
			{/each}
		</div>
	</div>
</div>

<style>
	/* Скрываем стандартный thumb браузера */
	input[type='range']::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 0;
		height: 0;
		background: transparent;
	}

	input[type='range']::-moz-range-thumb {
		width: 0;
		height: 0;
		background: transparent;
		border: none;
	}

	input[type='range']::-ms-thumb {
		width: 0;
		height: 0;
		background: transparent;
	}
</style>
