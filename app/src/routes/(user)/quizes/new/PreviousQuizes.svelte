<script lang="ts">
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';
	import { generateId } from '$lib/utils/generate-id';
		import { pb } from '$lib/pb';

	interface Props {
		inputText: string;
		attachedFiles: AttachedFile[];
		quizTemplateId: string;
		selectedDifficulty: string;
        questionCount: number;
		isDraft: boolean;
		searchQuery: string;
		onQuizSelected?: () => void;
	}

	let {quizTemplateId = $bindable(), inputText = $bindable(), attachedFiles = $bindable(), selectedDifficulty = $bindable(), questionCount = $bindable(), isDraft = $bindable(), searchQuery = $bindable(), onQuizSelected = () => {}}: Props = $props();

	const previousQuizes = $derived(quizesStore.quizes.filter((q: any) => q.status !== 'draft'));
	const filteredQuizes = $derived(previousQuizes.filter(q => q.title.toLowerCase().includes(searchQuery.toLowerCase()) || (q.query && q.query.toLowerCase().includes(searchQuery.toLowerCase()))));
	



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
		// Устанавливаем quizTemplateId
		quizTemplateId = quiz.id;

		// Устанавливаем текст

		inputText = quiz.query || '';


		// Восстанавливаем файлы из материалов
		if (quiz.materials && quiz.materials.length > 0) {
			const restoredFiles: AttachedFile[] = [];

			for (const materialId of quiz.materials) {
				// Пытаемся найти материал в локальном сторе
				const material = materialsStore.materials.find((m) => m.id === materialId);

				if (material && material.title) {
					restoredFiles.push(createAttachedFileFromMaterial(materialId, material.title));
				}
			}

			attachedFiles = restoredFiles;
		} else {
			// Если материалов нет, очищаем прикрепленные файлы
			attachedFiles = [];
		}

		onQuizSelected();
	}
</script>

<div class="border-base-200 h-full w-80 flex-shrink-0 overflow-y-auto border-r">
	
		

		<!-- Динамическая история квизов из store -->
		<div class="space-y-3">
			{#if filteredQuizes.length === 0}
				<div class="mt-8 text-center">
					<p class="text-sm">No previous quizes yet</p>
					<p class="mt-1 text-xs">Create your first quiz!</p>
				</div>
			{:else}
				{#each filteredQuizes as quiz}
					<div
						class="border-base-200 cursor-pointer rounded-lg border p-4 shadow-sm transition-shadow hover:shadow-md hover:bg-red-100 }"
						onclick={() => handleQuizClick(quiz)}
						onkeydown={(e) => e.key === 'Enter' && handleQuizClick(quiz)}
						role="button"
						tabindex="0"
					>
						<h3 class="mb-1 truncate font-medium text-left" title={quiz.title || `Quiz ${quiz.id}`}>
							{quiz.title || `Quiz ${quiz.id}`}
						</h3>
						<p class="mb-2 text-sm text-left">
							Quiz ID: {quiz.id}
						</p>
						{#if quiz.query}
							<p class="text-primary mb-1 text-xs text-left">
								<span class="font-medium">Query:</span>
								{quiz.query}
							</p>
						{/if}
						{#if quiz.materials && quiz.materials.length > 0}
							<p class="text-success text-xs text-left">
								<span class="font-medium">Materials:</span>
								{quiz.materials.length} file(s)
							</p>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>
