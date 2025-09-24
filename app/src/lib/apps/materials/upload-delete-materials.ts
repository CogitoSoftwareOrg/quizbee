import { pb } from '$lib/pb';
import type { MaterialsResponse } from '$lib/pb/pocketbase-types';


export async function uploadMaterial(file: File, title: string): Promise<MaterialsResponse> {
	
	const formData = new FormData();
	formData.append('file', file);
	formData.append('title', title);
	formData.append('user', pb!.authStore.model?.id || '');

	try {
		const material: MaterialsResponse = await pb!.collection('materials').create(formData);
		return material;
	} catch (error) {
		console.error('Error uploading material:', error);
		throw new Error(`Failed to upload material: ${error instanceof Error ? error.message : 'Unknown error'}`);
	}
}

/**
 * Удаляет материал из PocketBase
 * @param materialId - ID материала для удаления
 */
export async function deleteMaterial(materialId: string): Promise<void> {
	

	try {
		await pb!.collection('materials').delete(materialId);
	} catch (error) {
		console.error('Error deleting material:', error);
		throw new Error(`Failed to delete material: ${error instanceof Error ? error.message : 'Unknown error'}`);
	}
}