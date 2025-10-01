<script lang="ts">
	interface Props {
		selectedDifficulty?: string;
	}

	let { selectedDifficulty = $bindable('intermediate') }: Props = $props();
</script>

<div class="flex items-center justify-center gap-8">
	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			name="difficulty"
			value="beginner"
			bind:group={selectedDifficulty}
			class="radio radio-lg radio-success"
		/>
		<span class="text-md font-medium">Beginner</span>
	</label>
	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			name="difficulty"
			value="intermediate"
			bind:group={selectedDifficulty}
			class="radio radio-lg radio-warning"
		/>
		<span class="text-md font-medium">Intermediate</span>
	</label>
	<label class="flex cursor-pointer flex-col items-center gap-2">
		<input
			type="radio"
			name="difficulty"
			value="expert"
			bind:group={selectedDifficulty}
			class="radio radio-lg radio-error"
		/>
		<span class="text-md font-medium">Expert</span>
	</label>
</div>
