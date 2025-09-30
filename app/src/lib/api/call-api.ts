import { computeApiUrl } from './compute-url';

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export async function postApi(url: string, body: unknown) {
	return await callApi(url, 'POST', body);
}

export async function putApi(url: string, body: unknown) {
	return await callApi(url, 'PUT', body);
}

export async function patchApi(url: string, body: unknown) {
	return await callApi(url, 'PATCH', body);
}

async function callApi(url: string, method: Method, body: unknown) {
	const res = await fetch(`${computeApiUrl()}${url}`, {
		method,
		body: JSON.stringify(body),
		headers: {
			'Content-Type': 'application/json'
		},
		credentials: 'include'
	});

	if (!res.ok) {
		throw new Error(`Failed to call API: ${res.statusText} ${await res.text()}`);
	}

	return await res.json();
}
