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
</svelte:head>

<main class="relative flex h-full overflow-hidden flex-row">
    <div class="relative flex-1 overflow-y-auto overflow-x-hidden">
        <div class="mx-auto max-w-7xl py-4 sm:px-6 lg:px-8">
            <!-- Title Section -->
            <div class="mb-12 text-center">
                <div class="relative mx-auto inline-flex items-center justify-center">
                    <input
                        bind:value={title}
                        bind:this={inputElement}
                        type="text"
                        placeholder=""
                        class={`input input-xl rounded-lg text-center text-5xl font-semibold border-2 pt-3${title === 'Untitled Quiz' ? ' pr-8' : ''}`}
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
                                    
                        }}}
                    />
                    {#if title ==='Untitled Quiz'}
                        <div class="absolute pointer-events-none" style="left: 50%; transform: translateX(calc({title.length * 1}ch - 50% + 2ch)) translateY(-60%);">
                            <Pencil class="w-4 h-4 text-base-content/30" />
                        </div>
                    {/if}
                </div>
                {#if showWarningLength}
                    <p class="text-error mt-2 text-center">Title is limited to 30 characters.</p>
                {/if}
            </div>

            <!-- Describe Quiz Section -->
            <div class="mb-12 text-center">
                <div class=" flex items-center justify-center gap-2">
                    <h2 class="text-2xl font-semibold sm:text-3xl lg:text-4xl mb-2">Describe your quiz</h2>
                    
                </div>
                
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
                
                <div class="mx-auto w-full max-w-4xl">
                    <FileInput bind:attachedFiles bind:inputText bind:quizTemplateId />
                </div>
            </div>

            <!-- Settings Section -->
            <div class="mb-16">
                <div
                    class="mx-auto flex max-w-5xl flex-col items-center gap-8 lg:flex-row lg:justify-center lg:gap-16"
                >
                    <!-- Difficulty -->
                    <div class="w-full text-center lg:w-auto">
                        <div class="mb-6 flex items-center justify-center gap-2">
                            <h2 class="text-xl font-semibold sm:text-xl">Choose difficulty level</h2>
                        </div>
                        <DifficultySelector bind:selectedDifficulty />
                    </div>

                    <!-- Question Count -->
                    <div class="w-full ml-20 text-center lg:w-auto">
                        <div class="mb-6 flex items-center justify-center gap-2">
                            <h2 class="text-xl font-semibold sm:text-xl">Choose number of questions</h2>
                        </div>
                        <QuestionNumberSelector bind:value={questionCount} />
                    </div>
                </div>
            </div>

            <!-- Start Button -->
            <div class="flex justify-center pb-8">
                <StartQuizButton {quizTemplateId} {attachedFiles} {inputText} />
            </div>
        </div>
    </div>
</main>