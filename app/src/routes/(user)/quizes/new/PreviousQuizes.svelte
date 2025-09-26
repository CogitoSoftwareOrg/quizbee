<script lang="ts">
    import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
    import {quizesStore} from '$lib/apps/quizes/quizes.svelte'; 
    import { userStore } from '$lib/apps/users/user.svelte';
    import { materialsStore } from '$lib/apps/materials/materials.svelte';
    import { onMount } from 'svelte';
    import type { AttachedFile } from '$lib/types/attached-file';


    interface Props {
        inputText: string;
        attachedFiles: AttachedFile[];
    }

    let { inputText = $bindable(), attachedFiles = $bindable() }: Props = $props();

    let quizIds = $state<string[]>([]);

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
            uploadError: undefined,
            fromPreviousQuiz: true,
        };
    }

    // Функция для обработки клика по квизу
    async function handleQuizClick(quiz: any) {
        // Устанавливаем текст
        
        inputText = quiz.query ? quiz.query : '';
       
        
        // Восстанавливаем файлы из материалов
        if (quiz.materials && quiz.materials.length > 0) {
            const restoredFiles: AttachedFile[] = [];
            
            for (const materialId of quiz.materials) {
                // Пытаемся найти материал в локальном сторе
                const material = materialsStore.materials.find(m => m.id === materialId);
                
                if (material && material.title) {
                    restoredFiles.push(createAttachedFileFromMaterial(materialId, material.title));
                }
            }
            
            attachedFiles = restoredFiles;
        } else {
            // Если материалов нет, очищаем прикрепленные файлы
            attachedFiles = [];
        }
    }

    // Функция для форматирования времени
    function formatRelativeTime(dateString: string): string {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const diffWeeks = Math.floor(diffDays / 7);

        if (diffMinutes < 60) {
            return diffMinutes <= 1 ? 'just now' : `${diffMinutes} minutes ago`;
        } else if (diffHours < 24) {
            return diffHours === 1 ? '1 hour ago' : `${diffHours} hours ago`;
        } else if (diffDays < 7) {
            return diffDays === 1 ? '1 day ago' : `${diffDays} days ago`;
        } else {
            return diffWeeks === 1 ? '1 week ago' : `${diffWeeks} weeks ago`;
        }
    }

    // Функция для определения цвета бейджа на основе результата
    function getScoreColors(score: number): { bg: string; text: string } {
        if (score >= 80) return { bg: 'bg-success/10', text: 'text-success' };
        if (score >= 60) return { bg: 'bg-warning/10', text: 'text-warning' };
        return { bg: 'bg-error/10', text: 'text-error' };
    }

    // Функция для получения строки сложности
    function getDifficultyString(difficulty: string): string {
        const diffMap: Record<string, string> = {
            'beginner': 'Beginner',
            'intermediate': 'Intermediate', 
            'expert': 'Expert'
        };
        return diffMap[difficulty] || difficulty;
    }

    // Восстанавливаем объекты квизов по их ID
    const foundQuizes = $derived(
        // Фильтруем основной массив тестов из стора
        quizesStore.quizes.filter(quiz => 
            // Оставляем только те тесты, чей ID есть в нашем массиве `quizIds`
            quizIds.includes(quiz.id)
        )
    );

   
    $effect(() => {
        // Получаем массив попыток из хранилища
        const attempts = quizAttemptsStore.quizAttempts;
        
        // Извлекаем ID тестов (предполагая, что поле называется 'quiz')
        // Используем Set для получения только уникальных ID
        const uniqueQuizIds = new Set(attempts.map(attempt => attempt.quiz));
        
        quizIds = [...uniqueQuizIds];
    
    
      
    });
</script>

<div class="w-80 bg-base-100 border-r border-base-300 h-full overflow-y-auto flex-shrink-0">
    <div class="p-6">
        <h2 class="text-center text-xl font-bold mb-4 text-base-content">Previous quizes</h2>
        
        <!-- Динамическая история квизов из store -->
        <div class="space-y-3">
            {#if foundQuizes.length === 0}
                <div class="text-center text-base-content/60 mt-8">
                    <p class="text-sm">No previous quizes yet</p>
                    <p class="text-xs mt-1">Create your first quiz!</p>
                </div>
            {:else}
                {#each foundQuizes as quiz}
                    <div 
                        class="card card-body card-compact bg-base-100 hover:shadow-md transition-shadow cursor-pointer hover:bg-base-200"
                        onclick={() => handleQuizClick(quiz)}
                        onkeydown={(e) => e.key === 'Enter' && handleQuizClick(quiz)}
                        role="button"
                        tabindex="0"
                    >
                        <h3 class="font-medium text-base-content mb-1 truncate" title="{quiz.title || `Quiz ${quiz.id}`}">
                            {quiz.title || `Quiz ${quiz.id}`}
                        </h3>
                        <p class="text-sm text-base-content/60 mb-2">
                            Quiz ID: {quiz.id}
                        </p>
                        {#if quiz.query}
                            <p class="text-xs text-primary mb-1">
                                <span class="font-medium">Query:</span> {quiz.query}
                            </p>
                        {/if}
                        {#if quiz.materials && quiz.materials.length > 0}
                            <p class="text-xs text-success">
                                <span class="font-medium">Materials:</span> {quiz.materials.length} file(s)
                            </p>
                        {/if}
                    </div>
                {/each}
            {/if}
        </div>
    </div>
</div>