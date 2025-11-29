import { env } from '$env/dynamic/public';

export function computeEnvUrl(url: string) {
	console.log('env.PUBLIC_ENV', env.PUBLIC_ENV, url);
	if (env.PUBLIC_ENV === 'preview') {
		const base = new URL(url);
		const prIdCandidate = window.location.hostname.split('-')[0];
		if (/^\d+$/.test(prIdCandidate)) base.hostname = `${prIdCandidate}-${base.hostname}`;
		return base.toString();
	}
	console.log('env.PUBLIC_ENV', env.PUBLIC_ENV, url);
	return url;
}
