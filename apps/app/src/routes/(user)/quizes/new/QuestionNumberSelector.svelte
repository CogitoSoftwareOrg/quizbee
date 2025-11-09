<script lang="ts">
	let { value = $bindable(10) }: { value: number } = $props();

	const numbers = [10, 20, 30];
</script>

<div class="space-y-2">
	{#each numbers as num}
		<button
			type="button"
			onclick={() => (value = num)}
			class="flex w-full items-center gap-2 rounded-lg border-2 p-2 transition-all duration-100 md:gap-3 md:p-2.5 {value ===
			num
				? 'border-base-content bg-base-100 shadow-sm'
				: 'border-base-300 bg-base-100 hover:border-base-content/50 hover:bg-base-200/50'}"
		>
			<div class="text-2xl font-bold md:text-3xl">{num}</div>

			<div class="text-sm font-medium md:text-base">questions</div>

			{#if value === num}
				<div
					class="bg-base-content ml-auto flex h-4 w-4 items-center justify-center rounded-full md:h-5 md:w-5"
				>
					<div class="bg-base-100 h-1.5 w-1.5 rounded-full md:h-2 md:w-2"></div>
				</div>
			{/if}
		</button>
	{/each}
</div>
