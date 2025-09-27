<script lang="ts">
	import { quizesStore } from '$lib/apps/quizes/quizes.svelte';
	import { materialsStore } from '$lib/apps/materials/materials.svelte';
	import type { AttachedFile } from '$lib/types/attached-file';
	import { quizAttemptsStore } from '$lib/apps/quiz-attempts/quizAttempts.svelte';

	interface Props {
		inputText: string;
		attachedFiles: AttachedFile[];
	}

	let { inputText = $bindable(), attachedFiles = $bindable() }: Props = $props();

	const attemptQuizes = $derived(quizAttemptsStore.quizAttempts.filter((qa) => qa.feedback));
	const quizes = $derived(
		quizesStore.quizes.filter((q) => attemptQuizes.some((a) => a.quiz === q.id))
	);

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
	}
</script>

<div class="border-base-200 h-full w-80 flex-shrink-0 overflow-y-auto border-r">
	<div class="p-6">
		<h2 class="mb-4 text-center text-xl font-bold">Previous quizes templates</h2>

		<!-- Динамическая история квизов из store -->
		<div class="space-y-3">
			{#if quizes.length === 0}
				<div class="mt-8 text-center">
					<p class="text-sm">No previous quizes yet</p>
					<p class="mt-1 text-xs">Create your first quiz!</p>
				</div>
			{:else}
				{#each quizes as quiz}
					<div
						class="border-base-200 cursor-pointer rounded-lg border p-4 shadow-sm transition-shadow hover:shadow-md"
						onclick={() => handleQuizClick(quiz)}
						onkeydown={(e) => e.key === 'Enter' && handleQuizClick(quiz)}
						role="button"
						tabindex="0"
					>
						<h3 class="mb-1 truncate font-medium" title={quiz.title || `Quiz ${quiz.id}`}>
							{quiz.title || `Quiz ${quiz.id}`}
						</h3>
						<p class="mb-2 text-sm">
							Quiz ID: {quiz.id}
						</p>
						{#if quiz.query}
							<p class="text-primary mb-1 text-xs">
								<span class="font-medium">Query:</span>
								{quiz.query}
							</p>
						{/if}
						{#if quiz.materials && quiz.materials.length > 0}
							<p class="text-success text-xs">
								<span class="font-medium">Materials:</span>
								{quiz.materials.length} file(s)
							</p>
						{/if}
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>
