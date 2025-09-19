import type { MaterialsResponse } from './pocketbase-types';

export type UserExpand = {
	materials: MaterialsResponse[] | undefined;
};
