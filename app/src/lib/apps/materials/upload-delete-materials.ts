import { pb } from '$lib/pb';
import type { MaterialsResponse } from '$lib/pb/pocketbase-types';


export async function uploadMaterial(file: File, title: string): Promise<MaterialsResponse> {
	if (!pb) {
		throw new Error('PocketBase client is not initialized');
	}

	if (!pb.authStore.isValid) {
		throw new Error('User is not authenticated');
	}

	const formData = new FormData();
	formData.append('file', file);
	formData.append('title', title);
	formData.append('user', pb.authStore.model?.id || '');

	try {
		const material: MaterialsResponse = await pb.collection('materials').create(formData);
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
	if (!pb) {
		throw new Error('PocketBase client is not initialized');
	}

	if (!pb.authStore.isValid) {
		throw new Error('User is not authenticated');
	}

	try {
		await pb.collection('materials').delete(materialId);
	} catch (error) {
		console.error('Error deleting material:', error);
		throw new Error(`Failed to delete material: ${error instanceof Error ? error.message : 'Unknown error'}`);
	}
}