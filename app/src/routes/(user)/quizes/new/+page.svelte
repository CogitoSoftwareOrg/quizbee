<script lang="ts">
    import FileInput from './FileInput.svelte';
    import DifficultySelector from './DifficultySelector.svelte';
    import QuestionNumberSelector from './QuestionNumberSelector.svelte';
    import StartQuizButton from './StartQuizButton.svelte';
    import PreviousQuizes from './PreviousQuizes.svelte';
    import { materialsStore } from '$lib/apps/materials/materials.svelte';
    import { pb } from '$lib/pb';
    // import { computeApiUrl } from '$lib/api/compute-url';

    type AttachedFile = {
		file?: File;
		previewUrl: string | null;
		materialId?: string;
		material?: import('$lib/pb/pocketbase-types').MaterialsResponse;
		name: string;
		uploadPromise?: Promise<import('$lib/pb/pocketbase-types').MaterialsResponse>;
		isUploading?: boolean;
		uploadError?: string;
	};

    let attachedFiles = $state<AttachedFile[]>([]);
    let selectedDifficulty = $state('intermediate');
    let questionCount = $state(10);
    let inputText = $state('');

    /**
     * Создает AttachedFile объект из material ID без реального файла
     */
    function createAttachedFileFromMaterial(materialId: string, materialTitle: string): AttachedFile {
        // Извлекаем расширение из названия файла
        const extension = materialTitle.split('.').pop()?.toLowerCase() || '';
        
        // Проверяем, является ли файл изображением по расширению
        const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
        const isImage = imageExtensions.includes(extension);
        
        return {
            materialId: materialId,
            name: materialTitle,
            previewUrl: isImage ? null : null, // Для восстановленных файлов не показываем превью
            isUploading: false,
            uploadError: undefined
        };
    }

    /**
     * Обработчик выбора предыдущего квиза
     */
    async function handleQuizSelect(data: { query: string; materials?: string[] }) {
        // Устанавливаем текст
        inputText = data.query;
        
        // Восстанавливаем файлы из материалов
        if (data.materials && data.materials.length > 0) {
            const restoredFiles: AttachedFile[] = [];
            
            for (const materialId of data.materials) {
                // Пытаемся найти материал в локальном сторе
                const material = materialsStore.materials.find(m => m.id === materialId);
                
                if (material && material.title) {
                    restoredFiles.push(createAttachedFileFromMaterial(materialId, material.title));
                } else {
                    // Если материала нет в локальном сторе, пытаемся загрузить его
                    try {
                        const fetchedMaterial = await pb!.collection('materials').getOne(materialId);
                        
                        if (fetchedMaterial && fetchedMaterial.title) {
                            restoredFiles.push(createAttachedFileFromMaterial(materialId, fetchedMaterial.title));
                        }
                    } catch (error) {
                        console.error('Failed to fetch material:', materialId, error);
                        // Создаем файл с ID в качестве имени, если не удалось загрузить
                        restoredFiles.push(createAttachedFileFromMaterial(materialId, `Material ${materialId}`));
                    }
                }
            }
            
            attachedFiles = restoredFiles;
        } else {
            // Если материалов нет, очищаем прикрепленные файлы
            attachedFiles = [];
        }
    }


</script>

<svelte:head>
    <title>New Quiz</title>
</svelte:head>

<style>
    :global(*) {
        scrollbar-width: none !important;
        -ms-overflow-style: none !important;
    }
    
    :global(*::-webkit-scrollbar) {
        display: none !important;
    }
</style>

<main class="relative h-screen max-h-screen overflow-hidden overscroll-none flex">
    <!-- Левая колонка с историей квизов -->
    <PreviousQuizes onQuizSelect={handleQuizSelect} />
    
    <!-- Основная область контента -->
    <div class="flex-1 relative">
        <!-- Заголовок фиксированный сверху -->
        <div class="fixed top-16 left-1/2 transform -translate-x-1/2 z-10" style="left: calc(50% + 160px);">
            <h1 class="text-5xl font-bold text-center">New Quiz</h1>
        </div>
    
    <!-- Секция с описанием и FileInput -->
    <div class="fixed top-46 left-1/2 transform -translate-x-1/2 w-full max-w-6xl px-8 z-10" style="left: calc(50% + 160px); width: calc(100% - 320px); max-width: calc(1536px - 320px);">
        <div class="text-center">
            <div class="flex items-center justify-center gap-2">
                <h2 class="text-4xl font-semibold mb-1">Describe your quiz</h2>
                <div class="tooltip tooltip-bottom -mt-1 [&:before]:text-lg [&:before]:px-6 [&:before]:py-3 [&:before]:max-w-[30rem] [&:before]:whitespace-pre-line [&:before]:text-left"
                 data-tip="Describe your quiz in detail below, or simply attach files and we'll base the questions on their content. For the best results, do both!

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
                        class="text-gray-500 cursor-pointer transition-colors duration-200 hover:text-gray-700"
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
        
        <!-- Контейнер для размещения секций на одном уровне -->
        <div class="flex justify-center {attachedFiles.length > 5 ? 'mt-14' : 'mt-28'}">
            <div class="flex flex-col lg:flex-row lg:gap-16 xl:gap-24 items-center lg:items-start">
                <!-- Выбор уровня сложности -->
                <div class="text-center">
                    <div class="flex items-center justify-center gap-2">
                        <h2 class="text-2xl font-semibold mb-6">Choose difficulty level</h2>
                        <div class="tooltip tooltip-bottom -mt-6 [&:before]:text-lg [&:before]:px-6 [&:before]:py-3 [&:before]:max-w-md [&:before]:whitespace-pre-line [&:before]:text-left" data-tip="Choose your level based on your knowledge of the topic. Beginner gives you simple, basic questions, while Expert challenges you with tricky, thought-provoking ones.

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
                                class="text-gray-500 cursor-pointer transition-colors duration-200 hover:text-gray-700"
                            >
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 16v-4"/>
                                <path d="M12 8h.01"/>
                            </svg>
                        </div>
                    </div>
                    <DifficultySelector bind:selectedDifficulty />
                </div>

                <!-- Выбор количества вопросов -->
                <div class="text-center mt-10 lg:mt-0">
                    <div class="flex items-center justify-center gap-2">
                        <h2 class="text-2xl font-semibold mb-6">Choose number of questions</h2>
                        <div class="tooltip tooltip-bottom -mt-6 [&:before]:text-lg [&:before]:px-6 [&:before]:py-3 [&:before]:max-w-md [&:before]:whitespace-pre-line [&:before]:text-left"
                         data-tip="Each quiz question is a single-choice question with four answer options." >
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
                                class="text-gray-500 cursor-pointer transition-colors duration-200 hover:text-gray-700"
                            >
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M12 16v-4"/>
                                <path d="M12 8h.01"/>
                            </svg>
                        </div>
                    </div>
                    <QuestionNumberSelector bind:value={questionCount} />
                </div>
            </div>
        </div>
    </div>

    <!-- Кнопка создать квиз внизу -->
    <div class="fixed {attachedFiles.length > 5 ? 'bottom-20' : 'bottom-35'} left-1/2 transform -translate-x-1/2" style="left: calc(50% + 160px);">
        <StartQuizButton 
            {attachedFiles}
            {inputText}
            {selectedDifficulty}
            {questionCount}
        />
    </div>
    </div>
</main>