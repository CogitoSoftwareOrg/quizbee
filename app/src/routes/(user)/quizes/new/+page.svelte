<script lang="ts">
    import FileInput from './FileInput.svelte';
    import DifficultySelector from './DifficultySelector.svelte';
    // import { computeApiUrl } from '$lib/api/compute-url';

    let attachedFiles = $state<File[]>([]);
    let selectedDifficulty = $state('intermediate');
    let inputText = $state('');

    // Вычисляемое свойство для проверки активности кнопки
    const hasFiles = $derived(attachedFiles.length > 0);
    const hasText = $derived(inputText.trim().length > 0);
    const isSubmitDisabled = $derived(!hasFiles && !hasText);


  
    function handleSubmit() {
        console.log('Файлы:', attachedFiles);
        console.log('Сложность:', selectedDifficulty);
        console.log('Текст:', inputText);
        console.log('Количество файлов:', attachedFiles.length);
        console.log('Есть текст:', inputText.trim().length > 0);
    }


</script>

<svelte:head>
    <title>New Quiz</title>
</svelte:head>

<main class="relative min-h-screen overflow-hidden">
    <!-- Заголовок фиксированный сверху -->
    <div class="fixed top-16 left-1/2 transform -translate-x-1/2 z-10">
        <h1 class="main-title font-bold text-center">New Quiz</h1>
    </div>
    
    <!-- Секция с описанием и FileInput -->
    <div class="fixed top-46 left-1/2 transform -translate-x-1/2 w-full max-w-6xl px-8 z-10">
        <div class="text-center">
            <div class="flex items-center justify-center gap-2">
                <h2 class="quiz-title font-semibold mb-4">Describe your quiz</h2>
                <div class="tooltip tooltip-bottom -mt-3.5" data-tip="Describe your quiz in detail below, or simply attach files and we'll base the questions on their content. For the best results, do both!

                Feel free to attach presentations, PDFs, images, and more—we support a wide range of file types. For the most accurate questions, a few focused documents are more effective than many large ones." >
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
        </div>
        <div class="flex justify-center mt-4">
            <div class="w-full max-w-4xl">
                <FileInput bind:attachedFiles bind:inputText />      
            </div>
        </div>
        
        <!-- Выбор уровня сложности прямо под FileInput -->
        <div class="flex justify-center mt-12">
            <DifficultySelector bind:selectedDifficulty />
        </div>
    </div>

    <!-- Кнопка создать квиз внизу -->
    <div class="fixed bottom-35 left-1/2 transform -translate-x-1/2">
        <button 
            class="btn btn-primary px-16 py-8 text-3xl font-bold rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105" 
            disabled={isSubmitDisabled}
            onclick={handleSubmit}
        >
            Start a quiz 
        </button>
    </div>
</main>

<style>
    .main-title {
        font-size: 52px;
    }
    
    .quiz-title {
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