<script lang="ts">
	interface Props {
		selectedDifficulty?: string;
	}

	let { selectedDifficulty = $bindable('intermediate') }: Props = $props();

	const difficulties = [
		{ 
			value: 'beginner', 
			label: 'Beginner', 
			color: 'success'
		},
		{ 
			value: 'intermediate', 
			label: 'Intermediate', 
			color: 'warning'
		},
		{ 
			value: 'expert', 
			label: 'Expert', 
			color: 'error'
		}
	];

	function selectDifficulty(value: string) {
		selectedDifficulty = value;
	}
</script>

<div class="flex items-center justify-center gap-8">
	{#each difficulties as difficulty}
		<button
			type="button"
			onclick={() => selectDifficulty(difficulty.value)}
			class="flex cursor-pointer flex-col items-center gap-2 transition-all duration-200 hover:scale-105"
		>
			<div
				class="relative flex h-8 w-8 items-center justify-center rounded-full border-2 transition-all duration-200 {selectedDifficulty ===
				difficulty.value
					? `border-${difficulty.color} bg-${difficulty.color}`
					: 'border-base-content/30 bg-base-100 hover:border-base-content/50'}"
			>
			</div>
			<span
				class="text-md font-medium transition-colors {selectedDifficulty === difficulty.value
					? 'text-base-content'
					: 'text-base-content/70'}"
			>
				{difficulty.label}
			</span>
		</button>
	{/each}
</div>
