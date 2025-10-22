import { Preferences } from '@capacitor/preferences';
import PocketBase, { AsyncAuthStore } from 'pocketbase';
import { env } from '$env/dynamic/public';

import { computeEnvUrl } from '$lib/utils/compute-env-url';

import type { TypedPocketBase } from './pocketbase-types';

async function createPb(): Promise<TypedPocketBase> {
	const initial = (await Preferences.get({ key: 'pb_auth' })).value ?? '';
	const store = new AsyncAuthStore({
		initial,
		save: async (s) => Preferences.set({ key: 'pb_auth', value: s }),
		clear: async () => Preferences.remove({ key: 'pb_auth' })
	});
	return new PocketBase(computeEnvUrl(env.PUBLIC_PB_URL ?? ''), store) as TypedPocketBase;
}

export let pb: TypedPocketBase | undefined;
export const pbReady = createPb().then((inst) => (pb = inst));
