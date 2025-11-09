import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess({
		envDir: '../../envs'
	}),

	kit: {
		adapter: adapter({
			fallback: 'index.html'
		}),
		version: {
			pollInterval: 60_000
		}
	}
};

export default config;
