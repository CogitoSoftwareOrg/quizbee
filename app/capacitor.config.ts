import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
	appId: 'com.quizbee.app',
	appName: 'Quizbee',
	webDir: 'build',
	server: {
		url: 'https://app-quizbee.cogitosoftware.nl'
	}
};

export default config;
