<script lang="ts">
	let { value = $bindable(10) }: { value: number } = $props();

	const numbers = [10, 20, 30];
</script>

<div class="space-y-3">
	{#each numbers as num}
		<button
			type="button"
			onclick={() => (value = num)}
			class="flex w-full items-center gap-2 md:gap-3 rounded-lg border-2 p-2 md:p-2.5 transition-all duration-100 {value === num
				? 'border-base-content bg-base-100 shadow-sm'
				: 'border-base-300 bg-base-100 hover:border-base-content/50 hover:bg-base-200/50'}"
		>
			<div class="text-2xl md:text-3xl font-bold">{num}</div>

			<div class="text-sm md:text-base font-medium">questions</div>

			{#if value === num}
				<div class="bg-base-content ml-auto flex h-4 w-4 md:h-5 md:w-5 items-center justify-center rounded-full">
					<div class="bg-base-100 h-1.5 w-1.5 md:h-2 md:w-2 rounded-full"></div>
				</div>
			{/if}
		</button>
	{/each}
</div>
