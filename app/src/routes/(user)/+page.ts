import { goto } from '$app/navigation';

export const load = async () => {
	console.log('LOAD HOME');
	await goto('/home', { replaceState: true });
};
