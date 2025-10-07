<script lang="ts">
	import FileInput from './FileInput.svelte';
	import DifficultySelector from './DifficultySelector.svelte';
	import QuestionNumberSelector from './QuestionNumberSelector.svelte';
	import StartQuizButton from './StartQuizButton.svelte';
	import { tick } from 'svelte';
	import { onMount } from 'svelte';

	import Draft from './Draft.svelte';

	
	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import {  Pencil } from 'lucide-svelte';

	

	let quizTemplateId = $state<string>('');
	let title = $state<string>('');
	let attachedFiles = $state<AttachedFile[]>([]);
	let selectedDifficulty = $state('intermediate');
	let questionCount = $state(10);
	let inputText = $state('');
	let avoidRepeat = $state(false);

	let inputElement: HTMLInputElement;
	let showWarningLength = $state(false);

    let previousQuizes = $derived(quizesStore.quizes.filter((q: any) => q.status !== 'draft'));


	$effect(() => {
		if (inputElement && title) {
			inputElement.style.width = '0';
			inputElement.style.width = inputElement.scrollWidth + 5 + 'px';
		}
	});

	onMount(async () => {
		await tick();

		if (inputElement && title) {
			inputElement.style.width = '0';
			inputElement.style.width = inputElement.scrollWidth + 5 + 'px';
		}
	});
</script>

<svelte:head>
	<title>New Quiz</title>


	<style>
		@media (max-width: 1920px) {
			.quiz-container {
				zoom: 0.9;
			}
		}
	</style>


</svelte:head>

<main class="relative flex h-full overflow-y-auto flex-row">
    <div class="relative flex-1 ">
        <div class="min-h-screen flex items-start justify-center ">
            <div class="w-full max-w-3xl quiz-container">
                <!-- Header with Title -->
                <div class="text-center mb-9">
                    <div class="relative ml-5 -mt-3 mx-auto inline-flex items-center justify-center group ">
                        <input
                            bind:value={title}
                            bind:this={inputElement}
                            type="text"
                            placeholder=""
                            class="text-4xl md:text-5xl font-bold text-center border-none bg-transparent focus:outline-none focus:ring-0 px-0 leading-tight hover:text-warning transition-colors cursor-pointer"
                            style="width: auto; min-width: 300px;"
                            oninput={(e) => {
                                const target = e.target as HTMLInputElement;
                                const originalLength = target.value.length;
                                title = target.value.slice(0, 30);
                                showWarningLength = originalLength > 30;
                                target.style.width = '0';
                                target.style.width = target.scrollWidth + 5 + 'px';
                            }}
                            onblur={() => {
                                if (title.trim() === '') {
                                    title = 'Untitled Quiz';
                                }
                            }}
                        />
                        <Pencil class="w-6 h-6 text-base-content/40 opacity-0 group-hover:opacity-100 transition-opacity " />
                    </div>
                    {#if showWarningLength}
                        <p class="text-error text-center -mt-1">Title is limited to 30 characters.</p>
                    {:else}
                        <p class="text-base-content/60 text-lg -mt-3">Customize your quiz settings and get started</p>
                        <!-- Draft Component -->
                        <Draft
                            bind:title
                            bind:quizTemplateId
                            bind:inputText
                            bind:attachedFiles
                            bind:selectedDifficulty
                            bind:questionCount
                            bind:previousQuizes
                        />
                    {/if}
                </div>

                <!-- Main Card -->
                <div class="card bg-base-100 shadow-xl border-2 border-base-300 backdrop-blur-sm">
                    <div class="card-body p-6.5 ">
                        <!-- Description Section -->
                        <div class="mb-7">
                            
                            <div class="w-full">
                                <h3 class="text-base font-semibold mb-3 block">Describe your quiz</h3>
                                <FileInput bind:attachedFiles bind:inputText bind:quizTemplateId />
                            </div>
                        </div>

                        <!-- Difficulty and Questions Grid -->
                        <div class="grid md:grid-cols-2 gap-6 md:gap-8 mb-6">
                            <!-- Difficulty -->
                            <div>
                                <h3 class="text-base font-semibold mb-4 block">Choose difficulty level</h3>
                                <DifficultySelector bind:selectedDifficulty />
                            </div>

                            <!-- Question Count -->
                            <div>
                                <h3 class="text-base font-semibold mb-4 block">Number of questions</h3>
                                <QuestionNumberSelector bind:value={questionCount} />
                            </div>
                        </div>

                        <!-- Avoid Repeat Questions Section -->
                        {#if previousQuizes.length > 0}
                            <div class="mb-5 p-5 rounded-lg bg-base-200/50 border border-base-300">
                                <div class="flex items-center justify-between">
                                    <div class="flex-1">
                                        <h3 class="text-base font-semibold mb-1">Avoid repeating questions</h3>
                                        <p class="text-sm text-base-content/60">We prevent questions from your previous quizzes on similar topics from appearing again</p>
                                    </div>
                                    <label class="flex cursor-pointer gap-3 items-center ml-4">
                                        <span class="label-text font-medium {avoidRepeat ? 'text-base-content/50' : 'text-base-content'}">No</span>
                                        <input 
                                            type="checkbox" 
                                            bind:checked={avoidRepeat}
                                            class="toggle toggle-primary toggle-lg" 
                                        />
                                        <span class="label-text font-medium {avoidRepeat ? 'text-primary' : 'text-base-content/50'}">Yes</span>
                                    </label>
                                </div>
                            </div>
                        {/if}

                        <!-- Start Button -->
                        <StartQuizButton {quizTemplateId} {attachedFiles} {inputText} />
                    </div>
                </div>

                
            </div>
        </div>
    </div>
</main>