import { pb } from '$lib/pb';
import type { MaterialsResponse } from '$lib/pb/pocketbase-types';

class MaterialsStore {
	private _materials: MaterialsResponse[] = $state([]);

	get materials() {
		return this._materials;
	}
	set materials(materials: MaterialsResponse[]) {
		const sortedMaterials = materials.toSorted((a, b) => b.created.localeCompare(a.created));
		this._materials = sortedMaterials;
	}

	async subscribe(userId: string) {
		return pb!.collection('materials').subscribe(
			'*',
			(e) => {
				const material = e.record;
				switch (e.action) {
					case 'create':
						this._materials.unshift(material);
						break;
					case 'update':
						this._materials =
							this._materials?.map((m) => (m.id === material.id ? material : m)) || [];
						break;
					case 'delete':
						this._materials = this._materials?.filter((m) => m.id !== material.id) || [];
						break;
				}
			},
			{
				filter: `user = "${userId}"`
			}
		);
	}

	unsubscribe() {
		pb!.collection('materials').unsubscribe();
	}
}

export const materialsStore = new MaterialsStore();
