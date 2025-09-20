import { PUBLIC_API_URL } from '$env/static/public';

import { computeEnvUrl } from '$lib/utils/compute-env-url';

export function computeApiUrl() {
	return computeEnvUrl(PUBLIC_API_URL);
}
