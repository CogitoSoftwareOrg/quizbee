<script lang="ts">
	let { value = $bindable(10) }: { value: number } = $props();

	const numbers = [10, 20, 30, 50];

	function selectNumber(num: number) {
		value = num;
	}
</script>

<div class="grid grid-cols-2 gap-3">
	{#each numbers as num}
		<button
			type="button"
			onclick={() => selectNumber(num)}
			class="p-4 rounded-lg border-2 transition-all duration-200 {value === num
				? 'border-base-content bg-base-100 shadow-md scale-105'
				: 'border-base-300 bg-base-100 text-base-content hover:border-base-content/50 hover:bg-base-200/50'}"
		>
			<div class="text-3xl font-bold">{num}</div>
			<div class="text-xs mt-1 opacity-80">questions</div>
		</button>
	{/each}
</div>
