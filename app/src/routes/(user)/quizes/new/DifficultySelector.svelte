<script lang="ts">
	interface Props {
		selectedDifficulty?: string;
	}

	let { selectedDifficulty = $bindable('intermediate') }: Props = $props();

	const difficulties = [
		{
			value: 'beginner',
			label: 'Beginner',
			icon: '🌱',
			selectedClasses: 'border-success bg-success'
		},
		{
			value: 'intermediate',
			label: 'Intermediate',
			icon: '⚡',
			selectedClasses: 'border-warning bg-warning'
		},
		{
			value: 'expert',
			label: 'Expert',
			icon: '🎯',
			selectedClasses: 'border-error bg-error'
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
			class="flex w-full items-center gap-3 rounded-lg border-2 p-4 transition-all duration-100 {selectedDifficulty ===
			difficulty.value
				? 'border-base-content bg-primary/5 shadow-sm'
				: 'border-base-300 bg-base-100 hover:border-base-content/50 hover:bg-base-200/50'}"
		>
			<span class="text-2xl">{difficulty.icon}</span>
			<span
				class="text-base font-medium {selectedDifficulty === difficulty.value
					? 'text-base-content'
					: 'text-base-content'}"
			>
				{difficulty.label}
			</span>
			{#if selectedDifficulty === difficulty.value}
				<div class="bg-base-content ml-auto flex h-5 w-5 items-center justify-center rounded-full">
					<div class="bg-base-100 h-2 w-2 rounded-full"></div>
				</div>
			{/if}
		</button>
	{/each}
</div>
