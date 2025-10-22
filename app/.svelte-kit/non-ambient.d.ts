
// this file is generated — do not edit it


declare module "svelte/elements" {
	export interface HTMLAttributes<T> {
		'data-sveltekit-keepfocus'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-noscroll'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-preload-code'?:
			| true
			| ''
			| 'eager'
			| 'viewport'
			| 'hover'
			| 'tap'
			| 'off'
			| undefined
			| null;
		'data-sveltekit-preload-data'?: true | '' | 'hover' | 'tap' | 'off' | undefined | null;
		'data-sveltekit-reload'?: true | '' | 'off' | undefined | null;
		'data-sveltekit-replacestate'?: true | '' | 'off' | undefined | null;
	}
}

export {};


declare module "$app/types" {
	export interface AppTypes {
		RouteId(): "/(user)" | "/(auth)" | "/" | "/(user)/analytics" | "/(user)/attempts" | "/(user)/home" | "/(user)/profile" | "/(user)/quizes" | "/(user)/quizes/new" | "/(user)/quizes/[quizId]" | "/(user)/quizes/[quizId]/attempts" | "/(user)/quizes/[quizId]/attempts/[quizAttemptId]" | "/(user)/quizes/[quizId]/attempts/[quizAttemptId]/feedback" | "/(auth)/sign-in" | "/(auth)/sign-up";
		RouteParams(): {
			"/(user)/quizes/[quizId]": { quizId: string };
			"/(user)/quizes/[quizId]/attempts": { quizId: string };
			"/(user)/quizes/[quizId]/attempts/[quizAttemptId]": { quizId: string; quizAttemptId: string };
			"/(user)/quizes/[quizId]/attempts/[quizAttemptId]/feedback": { quizId: string; quizAttemptId: string }
		};
		LayoutParams(): {
			"/(user)": { quizId?: string; quizAttemptId?: string };
			"/(auth)": Record<string, never>;
			"/": { quizId?: string; quizAttemptId?: string };
			"/(user)/analytics": Record<string, never>;
			"/(user)/attempts": Record<string, never>;
			"/(user)/home": Record<string, never>;
			"/(user)/profile": Record<string, never>;
			"/(user)/quizes": { quizId?: string; quizAttemptId?: string };
			"/(user)/quizes/new": Record<string, never>;
			"/(user)/quizes/[quizId]": { quizId: string; quizAttemptId?: string };
			"/(user)/quizes/[quizId]/attempts": { quizId: string; quizAttemptId?: string };
			"/(user)/quizes/[quizId]/attempts/[quizAttemptId]": { quizId: string; quizAttemptId: string };
			"/(user)/quizes/[quizId]/attempts/[quizAttemptId]/feedback": { quizId: string; quizAttemptId: string };
			"/(auth)/sign-in": Record<string, never>;
			"/(auth)/sign-up": Record<string, never>
		};
		Pathname(): "/" | "/analytics" | "/analytics/" | "/attempts" | "/attempts/" | "/home" | "/home/" | "/profile" | "/profile/" | "/quizes" | "/quizes/" | "/quizes/new" | "/quizes/new/" | `/quizes/${string}` & {} | `/quizes/${string}/` & {} | `/quizes/${string}/attempts` & {} | `/quizes/${string}/attempts/` & {} | `/quizes/${string}/attempts/${string}` & {} | `/quizes/${string}/attempts/${string}/` & {} | `/quizes/${string}/attempts/${string}/feedback` & {} | `/quizes/${string}/attempts/${string}/feedback/` & {} | "/sign-in" | "/sign-in/" | "/sign-up" | "/sign-up/";
		ResolvedPathname(): `${"" | `/${string}`}${ReturnType<AppTypes['Pathname']>}`;
		Asset(): "/favicon.svg" | "/file-format-icons/pdf.svg" | "/fonts/League_Spartan/LeagueSpartan-VariableFont_wght.ttf" | "/fonts/League_Spartan/OFL.txt" | "/fonts/League_Spartan/README.txt" | "/fonts/League_Spartan/static/LeagueSpartan-Black.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-Bold.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-ExtraBold.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-ExtraLight.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-Light.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-Medium.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-Regular.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-SemiBold.ttf" | "/fonts/League_Spartan/static/LeagueSpartan-Thin.ttf" | "/fonts/Nunito/Nunito-Italic-VariableFont_wght.ttf" | "/fonts/Nunito/Nunito-VariableFont_wght.ttf" | "/fonts/Nunito/OFL.txt" | "/fonts/Nunito/README.txt" | "/fonts/Nunito/static/Nunito-Black.ttf" | "/fonts/Nunito/static/Nunito-BlackItalic.ttf" | "/fonts/Nunito/static/Nunito-Bold.ttf" | "/fonts/Nunito/static/Nunito-BoldItalic.ttf" | "/fonts/Nunito/static/Nunito-ExtraBold.ttf" | "/fonts/Nunito/static/Nunito-ExtraBoldItalic.ttf" | "/fonts/Nunito/static/Nunito-ExtraLight.ttf" | "/fonts/Nunito/static/Nunito-ExtraLightItalic.ttf" | "/fonts/Nunito/static/Nunito-Italic.ttf" | "/fonts/Nunito/static/Nunito-Light.ttf" | "/fonts/Nunito/static/Nunito-LightItalic.ttf" | "/fonts/Nunito/static/Nunito-Medium.ttf" | "/fonts/Nunito/static/Nunito-MediumItalic.ttf" | "/fonts/Nunito/static/Nunito-Regular.ttf" | "/fonts/Nunito/static/Nunito-SemiBold.ttf" | "/fonts/Nunito/static/Nunito-SemiBoldItalic.ttf" | "/fonts/Roboto/OFL.txt" | "/fonts/Roboto/README.txt" | "/fonts/Roboto/Roboto-Italic-VariableFont_wdth,wght.ttf" | "/fonts/Roboto/Roboto-VariableFont_wdth,wght.ttf" | "/fonts/Roboto/static/Roboto-Black.ttf" | "/fonts/Roboto/static/Roboto-BlackItalic.ttf" | "/fonts/Roboto/static/Roboto-Bold.ttf" | "/fonts/Roboto/static/Roboto-BoldItalic.ttf" | "/fonts/Roboto/static/Roboto-ExtraBold.ttf" | "/fonts/Roboto/static/Roboto-ExtraBoldItalic.ttf" | "/fonts/Roboto/static/Roboto-ExtraLight.ttf" | "/fonts/Roboto/static/Roboto-ExtraLightItalic.ttf" | "/fonts/Roboto/static/Roboto-Italic.ttf" | "/fonts/Roboto/static/Roboto-Light.ttf" | "/fonts/Roboto/static/Roboto-LightItalic.ttf" | "/fonts/Roboto/static/Roboto-Medium.ttf" | "/fonts/Roboto/static/Roboto-MediumItalic.ttf" | "/fonts/Roboto/static/Roboto-Regular.ttf" | "/fonts/Roboto/static/Roboto-SemiBold.ttf" | "/fonts/Roboto/static/Roboto-SemiBoldItalic.ttf" | "/fonts/Roboto/static/Roboto-Thin.ttf" | "/fonts/Roboto/static/Roboto-ThinItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Black.ttf" | "/fonts/Roboto/static/Roboto_Condensed-BlackItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Bold.ttf" | "/fonts/Roboto/static/Roboto_Condensed-BoldItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-ExtraBold.ttf" | "/fonts/Roboto/static/Roboto_Condensed-ExtraBoldItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-ExtraLight.ttf" | "/fonts/Roboto/static/Roboto_Condensed-ExtraLightItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Italic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Light.ttf" | "/fonts/Roboto/static/Roboto_Condensed-LightItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Medium.ttf" | "/fonts/Roboto/static/Roboto_Condensed-MediumItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Regular.ttf" | "/fonts/Roboto/static/Roboto_Condensed-SemiBold.ttf" | "/fonts/Roboto/static/Roboto_Condensed-SemiBoldItalic.ttf" | "/fonts/Roboto/static/Roboto_Condensed-Thin.ttf" | "/fonts/Roboto/static/Roboto_Condensed-ThinItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Black.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-BlackItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Bold.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-BoldItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-ExtraBold.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-ExtraBoldItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-ExtraLight.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-ExtraLightItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Italic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Light.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-LightItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Medium.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-MediumItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Regular.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-SemiBold.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-SemiBoldItalic.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-Thin.ttf" | "/fonts/Roboto/static/Roboto_SemiCondensed-ThinItalic.ttf" | "/fonts/Roboto-VariableFont.ttf" | "/fonts/Rubik/OFL.txt" | "/fonts/Rubik/README.txt" | "/fonts/Rubik/Rubik-Italic-VariableFont_wght.ttf" | "/fonts/Rubik/Rubik-VariableFont_wght.ttf" | "/fonts/Rubik/static/Rubik-Black.ttf" | "/fonts/Rubik/static/Rubik-BlackItalic.ttf" | "/fonts/Rubik/static/Rubik-Bold.ttf" | "/fonts/Rubik/static/Rubik-BoldItalic.ttf" | "/fonts/Rubik/static/Rubik-ExtraBold.ttf" | "/fonts/Rubik/static/Rubik-ExtraBoldItalic.ttf" | "/fonts/Rubik/static/Rubik-Italic.ttf" | "/fonts/Rubik/static/Rubik-Light.ttf" | "/fonts/Rubik/static/Rubik-LightItalic.ttf" | "/fonts/Rubik/static/Rubik-Medium.ttf" | "/fonts/Rubik/static/Rubik-MediumItalic.ttf" | "/fonts/Rubik/static/Rubik-Regular.ttf" | "/fonts/Rubik/static/Rubik-SemiBold.ttf" | "/fonts/Rubik/static/Rubik-SemiBoldItalic.ttf" | "/pwa-192.png" | "/pwa-512.png" | "/pwa-maskable.png" | "/robots.txt" | string & {};
	}
}