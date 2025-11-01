import { tick } from 'svelte';

export async function scrollToBottom(node: HTMLElement | null) {
	await tick();
	if (!node) return;
	node.scrollTo({
		top: node.scrollHeight,
		behavior: 'smooth'
	});
}
