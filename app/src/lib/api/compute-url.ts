import { env } from '$env/dynamic/public';

import { computeEnvUrl } from '$lib/utils/compute-env-url';

export function computeApiUrl() {
	return computeEnvUrl(env.PUBLIC_API_URL);
}
