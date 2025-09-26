<script lang="ts">
    import FileInput from './FileInput.svelte';
    import DifficultySelector from './DifficultySelector.svelte';
    import QuestionNumberSelector from './QuestionNumberSelector.svelte';
    import StartQuizButton from './StartQuizButton.svelte';
    import PreviousQuizes from './PreviousQuizes.svelte';
    import InfoIcon from '$lib/ui/InfoIcon.svelte';
    import type { AttachedFile } from '$lib/types/attached-file';


   

    let attachedFiles = $state<AttachedFile[]>([]);
    let selectedDifficulty = $state('intermediate');
    let questionCount = $state(10);
    let inputText = $state('');


</script>

<svelte:head>
    <title>New Quiz</title>
</svelte:head>


<main class="relative h-full flex">
    
    <PreviousQuizes 
        bind:inputText
        bind:attachedFiles
    />
    
    
    <div class="flex-1 relative py-16 px-8 overflow-y-auto">
        
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold">New Quiz</h1>
        </div>
    
    
    <div class="max-w-7xl mx-auto">
        <div class="text-center">
            <div class="flex items-center justify-center gap-2">
                <h2 class="text-4xl font-semibold mb-1">Describe your quiz</h2>
                <div class="tooltip tooltip-bottom -mt-1 [&:before]:text-lg [&:before]:px-6 [&:before]:py-3 [&:before]:max-w-[30rem] [&:before]:whitespace-pre-line [&:before]:text-left"
                 data-tip="Describe your quiz in detail below, or simply attach files and we'll base the questions on their content. For the best results, do both!

Feel free to attach presentations, PDFs, images, and more—we support a wide range of file types. For the most accurate questions, a few focused documents are more effective than many large ones." >
                    <InfoIcon />
                </div>
            </div>
        </div>
        <div class="flex justify-center mt-4 mb-12">
            <div class="w-full max-w-4xl">
                <FileInput bind:attachedFiles bind:inputText />      
            </div>
        </div>
        
        
        <div class="flex justify-center mb-16">
            <div class="flex flex-col lg:flex-row lg:gap-16 xl:gap-24 items-center lg:items-start">
                
                <div class="text-center">
                    <div class="flex items-center justify-center gap-2">
                        <h2 class="text-2xl font-semibold mb-6">Choose difficulty level</h2>
                        <div class="tooltip tooltip-bottom -mt-6 [&:before]:text-lg [&:before]:px-6 [&:before]:py-3 [&:before]:max-w-md [&:before]:whitespace-pre-line [&:before]:text-left" data-tip="Choose your level based on your knowledge of the topic. Beginner gives you simple, basic questions, while Expert challenges you with tricky, thought-provoking ones.

        And don't worry, if you feel that the questions are too hard or too easy you can adjust the difficulty during the quiz!" >
                            <InfoIcon />
                        </div>
                    </div>
                    <DifficultySelector bind:selectedDifficulty />
                </div>

                
                <div class="text-center mt-10 lg:mt-0">
                    <div class="flex items-center justify-center gap-2">
                        <h2 class="text-2xl font-semibold mb-6">Choose number of questions</h2>
                        <div class="tooltip tooltip-bottom -mt-6 [&:before]:text-lg [&:before]:px-6 [&:before]:py-3 [&:before]:max-w-md [&:before]:whitespace-pre-line [&:before]:text-left"
                         data-tip="Each quiz question is a single-choice question with four answer options." >
                            <InfoIcon />
                        </div>
                    </div>
                    <QuestionNumberSelector bind:value={questionCount} />
                </div>
            </div>
        </div>

        
        <div class="flex justify-center">
            <StartQuizButton 
                {attachedFiles}
                {inputText}
                {selectedDifficulty}
                {questionCount}
            />
        </div>
    </div>
    </div>
</main>