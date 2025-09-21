<script lang="ts">
    import FileInput from './FileInput.svelte';
    import { onMount, onDestroy } from 'svelte';

    let attachedFiles: FileList | null = null;
    let selectedDifficulty: string = '';
    let isGlobalDragging: boolean = false;
    let dragCounter: number = 0;
    let globalDroppedFiles: FileList | null = null;

    function handleSubmit() {
        console.log('Файлы:', attachedFiles);
        console.log('Сложность:', selectedDifficulty);
    }

    function handleGlobalDragEnter(event: DragEvent) {
        event.preventDefault();
        dragCounter++;
        if (dragCounter === 1) {
            isGlobalDragging = true;
        }
    }

    function handleGlobalDragLeave(event: DragEvent) {
        event.preventDefault();
        dragCounter--;
        if (dragCounter === 0) {
            isGlobalDragging = false;
        }
    }

    function handleGlobalDrop(event: DragEvent) {
        event.preventDefault();
        dragCounter = 0;
        isGlobalDragging = false;
        
        const files = event.dataTransfer?.files;
        if (files && files.length > 0) {
            globalDroppedFiles = files;
            // Сбрасываем после небольшой задержки, чтобы FileInput успел обработать
            setTimeout(() => {
                globalDroppedFiles = null;
            }, 100);
        }
    }

    function handleGlobalDragOver(event: DragEvent) {
        event.preventDefault();
    }

    onMount(() => {
        document.addEventListener('dragenter', handleGlobalDragEnter);
        document.addEventListener('dragleave', handleGlobalDragLeave);
        document.addEventListener('drop', handleGlobalDrop);
        document.addEventListener('dragover', handleGlobalDragOver);
    });

    onDestroy(() => {
        document.removeEventListener('dragenter', handleGlobalDragEnter);
        document.removeEventListener('dragleave', handleGlobalDragLeave);
        document.removeEventListener('drop', handleGlobalDrop);
        document.removeEventListener('dragover', handleGlobalDragOver);
    });
</script>

<svelte:head>
    <title>New Quiz</title>
</svelte:head>

<main class="relative min-h-screen overflow-hidden">
    <!-- Полноэкранный overlay для drag and drop -->
    {#if isGlobalDragging}
        <div class="fixed inset-0 z-50 bg-white flex items-center justify-center">
            <div class="text-center">
                <div class="text-4xl font-bold text-gray-800 mb-4">Drag and Drop</div>
                <div class="text-xl text-gray-600">You can drop the file anywhere on the screen</div>
            </div>
        </div>
    {/if}

    <!-- Заголовок фиксированный сверху -->
    <div class="fixed top-16 left-1/2 transform -translate-x-1/2 z-10">
        <h1 class="text-3xl font-bold text-center">New Quiz</h1>
    </div>
    
    <!-- Выбор уровня сложности ниже центра -->
    <div class="fixed top-2/3 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10">
        <div class="text-center">
            <h2 class="text-xl font-semibold mb-6">Choose difficulty level</h2>
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
    </div>

    <!-- Нижняя секция с FileInput и кнопкой - размещена внизу страницы -->
    <div class="fixed bottom-8 left-1/2 transform -translate-x-1/2 w-full max-w-6xl px-8">
        <div class="flex gap-6 items-center">
            <!-- FileInput контейнер -->
            <div class="flex-1 h-[200px] flex items-center">
                <FileInput globalFiles={globalDroppedFiles} />
            </div>
            
            <!-- Кнопка создать квиз -->
            <div class="flex-shrink-0 h-[65px] flex items-center">
                <button class="btn btn-primary px-8 py-4 text-lg h-full" on:click={handleSubmit}>
                    Start a quiz 
                </button>
            </div>
        </div>
    </div>
</main>

<style>
   
    
    /* Убираем обводки у всех элементов на всякий случай */
    * {
        box-shadow: none !important;
    }
    
    div:focus {
        outline: none !important;
    }
</style>