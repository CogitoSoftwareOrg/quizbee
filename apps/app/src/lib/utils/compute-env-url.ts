import { env } from '$env/dynamic/public';

export function computeEnvUrl(url: string) {
	if (env.PUBLIC_ENV === 'preview') {
		const base = new URL(url);
		const prIdCandidate = window.location.hostname.split('-')[0];
		if (/^\d+$/.test(prIdCandidate)) base.hostname = `${prIdCandidate}-${base.hostname}`;
		return base.toString();
	}
	return url;
}
