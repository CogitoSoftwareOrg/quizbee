import { tick } from 'svelte';

const portalMap = new Map();

export function createPortal(node: HTMLElement, id = 'default') {
	const key = `$$portal.${id}`;
	if (portalMap.has(key)) throw `duplicate portal key "${id}"`;
	else portalMap.set(key, node);
	return { destroy: () => portalMap.delete(key) };
}
function mount(node: HTMLElement, key: string) {
	if (!portalMap.has(key)) throw `unknown portal ${key}`;
	const host = portalMap.get(key);
	host.appendChild(node);
	return () => host.contains(node) && host.removeChild(node);
}

async function waitForPortal(key: string, maxAttempts = 10): Promise<void> {
	for (let i = 0; i < maxAttempts; i++) {
		if (portalMap.has(key)) return;
		await tick();
	}
	throw `portal ${key} not found after ${maxAttempts} attempts`;
}

export function portal(node: HTMLElement, id = 'default') {
	let destroy: (() => void) | undefined;
	const key = `$$portal.${id}`;
	if (!portalMap.has(key)) {
		waitForPortal(key)
			.then(() => {
				destroy = mount(node, key);
			})
			.catch((err) => {
				console.error('Portal mount error:', err);
			});
	} else {
		destroy = mount(node, key);
	}
	return { destroy: () => destroy?.() };
}
