<script lang="ts">
	interface Props {
		selectedDifficulty?: string;
	}

	let { selectedDifficulty = $bindable('intermediate') }: Props = $props();

	const difficulties = [
		{ 
			value: 'beginner', 
			label: 'Beginner', 
			icon: '🌱'
		},
		{ 
			value: 'intermediate', 
			label: 'Intermediate', 
			icon: '⚡'
		},
		{ 
			value: 'expert', 
			label: 'Expert', 
			icon: '🎯'
		}
	];

	function selectDifficulty(value: string) {
		selectedDifficulty = value;
	}
</script>

<div class="space-y-3">
	{#each difficulties as difficulty}
		<button
			type="button"
			onclick={() => selectDifficulty(difficulty.value)}
			class="w-full flex items-center gap-3 p-4 rounded-lg border-2 transition-all duration-100 {selectedDifficulty ===
			difficulty.value
				? 'border-base-content bg-primary/5 shadow-sm'
				: 'border-base-300 bg-base-100 hover:border-base-content/50 hover:bg-base-200/50'}"
		>
			<span class="text-2xl">{difficulty.icon}</span>
			<span
				class="font-medium text-base {selectedDifficulty === difficulty.value
					? 'text-base-content'
					: 'text-base-content'}"
			>
				{difficulty.label}
			</span>
			{#if selectedDifficulty === difficulty.value}
				<div class="ml-auto w-5 h-5 rounded-full bg-base-content flex items-center justify-center">
					<div class="w-2 h-2 rounded-full bg-base-100"></div>
				</div>
			{/if}
		</button>
	{/each}
</div>
