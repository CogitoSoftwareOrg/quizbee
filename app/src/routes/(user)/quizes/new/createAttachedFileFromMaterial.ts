import type { AttachedFile } from '$lib/types/attached-file';
import { materialsStore } from '$lib/apps/materials/materials.svelte';


function createAttachedFileFromMaterial(materialId: string, draftStatus: string): AttachedFile {
		// Извлекаем расширение из названия файла
        const material = materialsStore.materials.find((m) => m.id === materialId);
		const extension = material!.title.split('.').pop()?.toLowerCase() || '';
		// Проверяем, является ли файл изображением по расширению
		const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
		const isImage = imageExtensions.includes(extension);

		return {
			materialId: materialId,
			name: material!.title,
			previewUrl: isImage ? null : null, // Для восстановленных файлов не показываем превью
			isUploading: false,
			uploadError: undefined,
            deletionAllowed: draftStatus === 'draft'? true : false,
		};
	}
export { createAttachedFileFromMaterial };