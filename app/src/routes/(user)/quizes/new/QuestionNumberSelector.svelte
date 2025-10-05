<script lang="ts">
	let { value = $bindable(10) }: { value: number } = $props();

	const numbers = [10, 20, 30, 50];

	function selectNumber(num: number) {
		value = num;
	}
</script>

<div class="flex items-center justify-center gap-13">
	{#each numbers as num}
		<button
			type="button"
			onclick={() => selectNumber(num)}
			class="flex cursor-pointer flex-col items-center gap-2 transition-all duration-200 hover:scale-105"
		>
			<div
				class="relative flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all duration-200 {value ===
				num
					? 'border-warning bg-warning'
					: 'border-base-content/30 bg-base-100 hover:border-base-content/50'}"
			>
			</div>
			<span
				class="text-md font-medium transition-colors {value === num
					? 'text-base-content'
					: 'text-base-content/70'}"
			>
				{num}
			</span>
		</button>
	{/each}
</div>
