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

  return next();
});
