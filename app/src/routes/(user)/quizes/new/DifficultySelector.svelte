<script lang="ts">
    interface Props {
        selectedDifficulty?: string;
    }

    let { selectedDifficulty = $bindable('intermediate') }: Props = $props();
</script>

<div class="flex gap-8 items-center justify-center">
    <label class="flex flex-col items-center gap-2 cursor-pointer">
        <input 
            type="radio" 
            name="difficulty" 
            value="beginner" 
            bind:group={selectedDifficulty}
            class="radio radio-success radio-lg" 
        />
        <span class="text-md font-medium">Beginner</span>
    </label>
    <label class="flex flex-col items-center gap-2 cursor-pointer">
        <input 
            type="radio" 
            name="difficulty" 
            value="intermediate" 
            bind:group={selectedDifficulty}
            class="radio radio-warning radio-lg" 
        />
        <span class="text-md font-medium">Intermediate</span>
    </label>
    <label class="flex flex-col items-center gap-2 cursor-pointer">
        <input 
            type="radio" 
            name="difficulty" 
            value="expert" 
            bind:group={selectedDifficulty}
            class="radio radio-error radio-lg" 
        />
        <span class="text-md font-medium">Expert</span>
    </label>
</div>