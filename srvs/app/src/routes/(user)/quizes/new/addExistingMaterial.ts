import type { AttachedFile } from '$lib/types/attached-file';
import { pb } from '$lib/pb';
import { materialsStore } from '$lib/apps/materials/materials.svelte';

async function addExistingMaterial(materialId: string, quizTemplateId: string) {
	console.log(materialsStore.materials);
	const material = materialsStore.materials.find((m) => m.id === materialId);
	const attachedFile: AttachedFile = {
		name: material!.title,
		isUploading: false,
		isIndexing: false,
		materialId: material!.id,
		tokens: material!.tokens || 0,
		isBook: material!.isBook || false,
		previewUrl:
			material!.file && /\.(jpg|jpeg|png|gif|webp)$/i.test(material!.file)
				? pb!.files.getURL(material!, material!.file)
				: null
	};

	if (quizTemplateId) {
		try {
			const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
			const updatedMaterials = [...(quiz.materials || []), material!.id];
			await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
		} catch (error) {
			console.error('Failed to attach material to quiz:', error);
		}
	}
	return attachedFile;
}
export { addExistingMaterial };
