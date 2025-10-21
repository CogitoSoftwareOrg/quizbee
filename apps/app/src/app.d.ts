// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces

import type { QuizAttemptsResponse } from '$lib/pb';

declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		interface PageState {
			attempt?: QuizAttemptsResponse;
		}
		// interface Platform {}
	}
}

export {};
