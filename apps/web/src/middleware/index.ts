import { defineMiddleware } from "astro:middleware";

import { pb } from "@/lib";
import { languages, defaultLang } from "@/i18n/ui";

export const onRequest = defineMiddleware(async (context, next) => {
  if (!pb.authStore.isValid) {
    await pb
      .collection("_superusers")
      .authWithPassword(
        import.meta.env.PB_EMAIL ?? process.env.RUNTIME_PB_EMAIL,
        import.meta.env.PB_PASSWORD ?? process.env.RUNTIME_PB_PASSWORD
      );
  }

  // Handle locale routing
  const pathname = context.url.pathname;

  // Skip static files and assets
  if (
    pathname.startsWith("/_") ||
    pathname.includes(".") ||
    pathname.startsWith("/fonts/") ||
    pathname.startsWith("/file-format-icons/")
  ) {
    return next();
  }

  const [, firstSegment] = pathname.split("/");

  // Redirect root to default language
  if (pathname === "/") {
    return context.redirect(`/${defaultLang}/`, 302);
  }

  // Check if first segment is a valid locale
  if (firstSegment && !(firstSegment in languages)) {
    // If it's not a valid locale, redirect to default locale
    return context.redirect(`/${defaultLang}${pathname}`, 302);
  }

  return next();
});
