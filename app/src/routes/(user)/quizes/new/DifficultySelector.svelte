<script lang="ts">
	interface Props {
		selectedDifficulty?: string;
	}

	let { selectedDifficulty = $bindable('intermediate') }: Props = $props();

	const difficulties = [
		{
			value: 'beginner',
			label: 'Beginner',
			selectedClasses: 'border-success bg-success'
		},
		{
			value: 'intermediate',
			label: 'Intermediate',
			selectedClasses: 'border-warning bg-warning'
		},
		{
			value: 'expert',
			label: 'Expert',
			selectedClasses: 'border-error bg-error'
		}
	];

	function selectDifficulty(value: string) {
		selectedDifficulty = value;
	}
</script>

<div class="flex items-center justify-center gap-5 sm:gap-6 md:gap-8">
	{#each difficulties as difficulty}
		<button
			type="button"
			onclick={() => selectDifficulty(difficulty.value)}
			class="flex min-w-0 cursor-pointer flex-col items-center gap-1.5 transition-all duration-200 hover:scale-105 sm:gap-2"
		>
			<div
				class="relative flex size-7 items-center justify-center rounded-full border-2 transition-all duration-200 sm:size-8 {selectedDifficulty ===
				difficulty.value
					? difficulty.selectedClasses
					: 'border-base-content/30 bg-base-100 hover:border-base-content/50'}"
			></div>
			<span
				class="text-xs font-medium transition-colors sm:text-sm {selectedDifficulty ===
				difficulty.value
					? 'text-base-content'
					: 'text-base-content/70'}"
			>
				{difficulty.label}
			</span>
		</button>
	{/each}
</div>
