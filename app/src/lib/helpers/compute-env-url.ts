import { PUBLIC_ENV, PUBLIC_COOLIFY_URL } from '$env/static/public';

export function computeEnvUrl(url: string) {
	if (PUBLIC_ENV === 'preview') {
		const base = new URL(url);
		const coolifyUrl = new URL(PUBLIC_COOLIFY_URL);
		const prIdCandidate = coolifyUrl.hostname.split('-')[0];
		if (/^\d+$/.test(prIdCandidate)) base.hostname = `${prIdCandidate}-${base.hostname}`;
		return base.toString();
	}
	return url;
}
