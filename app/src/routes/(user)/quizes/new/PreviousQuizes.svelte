<script lang="ts">
    import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
    import {quizesStore} from '$lib/apps/quizes/quizes.svelte'; 
    import { userStore } from '$lib/apps/users/user.svelte';
    import { materialsStore } from '$lib/apps/materials/materials.svelte';
    import { onMount } from 'svelte';
    import type { AttachedFile } from '$lib/types/AttachedFile';


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
            uploadError: undefined
        };
    }

    // Функция для обработки клика по квизу
    async function handleQuizClick(quiz: any) {
        // Устанавливаем текст
        if (quiz.query) {
            inputText = quiz.query;
        }
        
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
        if (score >= 80) return { bg: 'bg-green-100', text: 'text-green-800' };
        if (score >= 60) return { bg: 'bg-yellow-100', text: 'text-yellow-800' };
        return { bg: 'bg-red-100', text: 'text-red-800' };
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

    onMount(() => {
        // Подписываемся на обновления квизов если пользователь авторизован
        if (userStore.user?.id) {
            quizAttemptsStore.subscribe(userStore.user.id);
            materialsStore.subscribe(userStore.user.id);
        }

        // Используем $effect для реакции на изменения в хранилище
        $effect(() => {
            // Получаем массив попыток из хранилища
            const attempts = quizAttemptsStore.quizAttempts;
            
            // Извлекаем ID тестов (предполагая, что поле называется 'quiz')
            // Используем Set для получения только уникальных ID
            const uniqueQuizIds = new Set(attempts.map(attempt => attempt.quiz));
            
            quizIds = [...uniqueQuizIds];
        });
        
        return () => {
            // Отписываемся при размонтировании компонента
            quizAttemptsStore.unsubscribe();
            materialsStore.unsubscribe();
        };
    });
</script>

<div class="w-80 bg-gray-50 border-r border-gray-200 h-full overflow-y-auto flex-shrink-0">
    <div class="p-6">
        <h2 class="text-center text-xl font-bold mb-4 text-gray-800">Previous quizes</h2>
        
        <!-- Динамическая история квизов из store -->
        <div class="space-y-3">
            {#if foundQuizes.length === 0}
                <div class="text-center text-gray-500 mt-8">
                    <p class="text-sm">No previous quizes yet</p>
                    <p class="text-xs mt-1">Create your first quiz!</p>
                </div>
            {:else}
                {#each foundQuizes as quiz}
                    <div 
                        class="bg-white rounded-lg p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer"
                        onclick={() => handleQuizClick(quiz)}
                        onkeydown={(e) => e.key === 'Enter' && handleQuizClick(quiz)}
                        role="button"
                        tabindex="0"
                    >
                        <h3 class="font-medium text-gray-900 mb-1 truncate" title="{quiz.title || `Quiz ${quiz.id}`}">
                            {quiz.title || `Quiz ${quiz.id}`}
                        </h3>
                        <p class="text-sm text-gray-500 mb-2">
                            Quiz ID: {quiz.id}
                        </p>
                        {#if quiz.query}
                            <p class="text-xs text-blue-600 mb-1">
                                <span class="font-medium">Query:</span> {quiz.query}
                            </p>
                        {/if}
                        {#if quiz.materials && quiz.materials.length > 0}
                            <p class="text-xs text-green-600">
                                <span class="font-medium">Materials:</span> {quiz.materials.length} file(s)
                            </p>
                        {/if}
                    </div>
                {/each}
            {/if}
        </div>
    </div>
</div>