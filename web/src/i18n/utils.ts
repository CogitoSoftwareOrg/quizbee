import { getCollection } from "astro:content";
import type { CollectionEntry } from "astro:content";

import { ui, defaultLang, showDefaultLang } from "./ui";

export function getLangFromUrl(url: URL) {
  const [, lang] = url.pathname.split("/");
  if (lang in ui) return lang as keyof typeof ui;
  return defaultLang;
}

export function useTranslations(lang: keyof typeof ui) {
  return function t(key: keyof (typeof ui)[typeof defaultLang]) {
    return ui[lang][key] || ui[defaultLang][key];
  };
}

export function useTranslatedPath(lang: keyof typeof ui) {
  return function translatePath(path: string, l: string = lang) {
    return !showDefaultLang && l === defaultLang ? path : `/${l}${path}`;
  };
}

// Get path without language prefix
export function getPathWithoutLang(pathname: string, currentLang: string) {
  if (currentLang === defaultLang && !showDefaultLang) {
    return pathname;
  }
  const regex = new RegExp(`^/${currentLang}(/|$)`);
  return pathname.replace(regex, "/");
}

// Get path with new language
export function getPathWithLang(
  pathname: string,
  newLang: string,
  lang: string
) {
  const pathWithoutLang = getPathWithoutLang(pathname, lang);
  if (newLang === defaultLang && !showDefaultLang) {
    return pathWithoutLang;
  }
  return `/${newLang}${pathWithoutLang}`;
}

// export async function getLandingContent(
//   lang: keyof typeof ui,
//   landingName: string = "quizbee-base"
// ): Promise<CollectionEntry<"landings">["data"]> {
//   const entries = await getCollection("landings");
//   console.log(entries);
//   const entry = entries.find(
//     (e: CollectionEntry<"landings">) => e.id === `${lang}/${landingName}.json`
//   );

//   if (!entry) {
//     // Fallback to default language if translation not found
//     const fallbackEntry = entries.find(
//       (e: CollectionEntry<"landings">) =>
//         e.id === `${defaultLang}/${landingName}.json`
//     );
//     if (!fallbackEntry) {
//       throw new Error(
//         `Landing content not found for: ${lang}/${landingName}.json`
//       );
//     }
//     return fallbackEntry.data;
//   }

//   return entry.data;
// }

// /**
//  * Get page content with automatic fallback to default language
//  * Returns the content along with fallback information
//  */
// export async function getPageContent(
//   lang: keyof typeof ui,
//   pageName: string
// ): Promise<{
//   data: CollectionEntry<"pages">["data"];
//   isFallback: boolean;
//   actualLang: keyof typeof ui;
// }> {
//   const entries = await getCollection("pages");
//   let entry = entries.find((e) => e.id === `${lang}/${pageName}`);
//   let isFallback = false;

//   // Fallback to default language if translation doesn't exist
//   if (!entry) {
//     entry = entries.find((e) => e.id === `${defaultLang}/${pageName}`);
//     isFallback = true;
//   }

//   if (!entry) {
//     throw new Error(`Page content not found for: ${pageName}`);
//   }

//   return {
//     data: entry.data,
//     isFallback,
//     actualLang: isFallback ? defaultLang : lang,
//   };
// }
