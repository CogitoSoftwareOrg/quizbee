import type { AttachedFile } from '$lib/types/attached-file';

import { pb } from '$lib/pb';

async function removeFile(index: number, attachedFiles: AttachedFile[], quizTemplateId: string) {
	const fileToRemove = attachedFiles[index];

	if (fileToRemove.previewUrl) {
		URL.revokeObjectURL(fileToRemove.previewUrl);
	}

	if (quizTemplateId) {
		try {
			const quiz = await pb!.collection('quizes').getOne(quizTemplateId);
			const updatedMaterials = (quiz.materials || []).filter(
				(id: string) => id !== fileToRemove.materialId
			);
			await pb!.collection('quizes').update(quizTemplateId, { materials: updatedMaterials });
		} catch (error) {
			console.error('Failed to detach material from quiz:', error);
		}
	}

	if (fileToRemove.materialId) {
		try {
			const material = await pb!.collection('materials').getOne(fileToRemove.materialId);
			if (material.status !== 'used') {
				await pb!.collection('materials').delete(fileToRemove.materialId);
			}
		} catch (error) {
			console.error('Failed to delete material:', error);
		}
	}

	attachedFiles.splice(index, 1);
	return attachedFiles;
}

export { removeFile };
