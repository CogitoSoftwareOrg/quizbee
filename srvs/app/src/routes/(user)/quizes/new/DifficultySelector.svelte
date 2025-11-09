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

<div class="space-y-2">
	{#each difficulties as difficulty}
		<button
			type="button"
			onclick={() => selectDifficulty(difficulty.value)}
			class="flex w-full items-center gap-2 rounded-lg border-2 p-2 transition-all duration-100 md:gap-3 md:p-3 {selectedDifficulty ===
			difficulty.value
				? 'border-base-content bg-base-100 shadow-sm'
				: 'border-base-300 bg-base-100 hover:border-base-content/50 hover:bg-base-200/50'}"
		>
			<span class="text-xl md:text-2xl">{difficulty.icon}</span>
			<span
				class="text-sm font-medium md:text-base {selectedDifficulty === difficulty.value
					? 'text-base-content'
					: 'text-base-content'}"
			>
				{difficulty.label}
			</span>
			{#if selectedDifficulty === difficulty.value}
				<div
					class="bg-base-content ml-auto flex h-4 w-4 items-center justify-center rounded-full md:h-5 md:w-5"
				>
					<div class="bg-base-100 h-1.5 w-1.5 rounded-full md:h-2 md:w-2"></div>
				</div>
			{/if}
		</button>
	{/each}
</div>
