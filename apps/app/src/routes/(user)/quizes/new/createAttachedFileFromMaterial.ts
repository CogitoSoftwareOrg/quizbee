import type { AttachedFile } from '$lib/types/attached-file';
import { materialsStore } from '$lib/apps/materials/materials.svelte';

function createAttachedFileFromMaterial(materialId: string): AttachedFile {
	const material = materialsStore.materials.find((m) => m.id === materialId);
	const extension = material!.title.split('.').pop()?.toLowerCase() || '';

	const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg'];
	const isImage = imageExtensions.includes(extension);

	return {
		materialId: materialId,
		name: material!.title,
		previewUrl: isImage ? null : null,
		isUploading: false
	};
}
export { createAttachedFileFromMaterial };
