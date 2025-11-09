module.exports = {
	content: [
		'./src/**/*.{html,svelte,js,ts}',
		'./src/**/**/*.{html,svelte,js,ts}',
		'../../**/src/**/*.{html,svelte,js,ts}'
	],
	theme: {
		extend: {
			screens: {
				'3xl': '1920px',
				'4xl': '2560px',
				'5xl': '3840px'
			}
		}
	},
	plugins: []
};
