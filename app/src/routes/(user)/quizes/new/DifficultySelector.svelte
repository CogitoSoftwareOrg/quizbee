<script lang="ts">
    interface Props {
        selectedDifficulty?: string;
    }

    let { selectedDifficulty = $bindable('intermediate') }: Props = $props();
</script>

<div class="text-center">
    <div class="flex items-center justify-center gap-2">
        <h2 class="difficulty-title font-semibold mb-6">Choose difficulty level</h2>
        <div class="tooltip tooltip-bottom -mt-6" data-tip="Select your challenge. Beginner is perfect if you're new to the topic. Intermediate is for those who feel confident with the basics. Ready to tackle the trickiest questions? Choose Expert. 

        And don't worry, if you feel that the questions are too hard or too easy you can adjust the difficulty during the quiz!" >
            <svg 
                xmlns="http://www.w3.org/2000/svg" 
                width="28" 
                height="28" 
                viewBox="0 0 24 24" 
                fill="none" 
                stroke="currentColor" 
                stroke-width="2" 
                stroke-linecap="round" 
                stroke-linejoin="round" 
                class="info-icon"
            >
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 16v-4"/>
                <path d="M12 8h.01"/>
            </svg>
        </div>
    </div>
    <div class="flex gap-8 items-center justify-center">
        <label class="flex flex-col items-center gap-2 cursor-pointer">
            <input 
                type="radio" 
                name="difficulty" 
                value="beginner" 
                bind:group={selectedDifficulty}
                class="radio radio-success radio-lg" 
            />
            <span class="text-sm font-medium">Beginner</span>
        </label>
        <label class="flex flex-col items-center gap-2 cursor-pointer">
            <input 
                type="radio" 
                name="difficulty" 
                value="intermediate" 
                bind:group={selectedDifficulty}
                class="radio radio-warning radio-lg" 
            />
            <span class="text-sm font-medium">Intermediate</span>
        </label>
        <label class="flex flex-col items-center gap-2 cursor-pointer">
            <input 
                type="radio" 
                name="difficulty" 
                value="expert" 
                bind:group={selectedDifficulty}
                class="radio radio-error radio-lg" 
            />
            <span class="text-sm font-medium">Expert</span>
        </label>
    </div>
</div>

<style>
    .difficulty-title {
        font-size: 32px;
    }
    
    .info-icon {
        color: #6b7280;
        cursor: pointer;
        transition: color 0.2s ease;
    }
    
    .info-icon:hover {
        color: #374151;
    }
    
    .tooltip:before {
        font-size: 17px !important;
        padding: 13px 25px !important;
        max-width: 450px !important;
        white-space: pre-line !important;
        text-align: left !important;
    }
</style>