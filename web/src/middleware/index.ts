import { defineMiddleware } from "astro:middleware";

import { pb } from "@/lib";

export const onRequest = defineMiddleware((context, next) => {
  if (!pb.authStore.isValid) {
    pb.collection("_superusers").authWithPassword(
      import.meta.env.PB_EMAIL,
      import.meta.env.PB_PASSWORD
    );
  }

  return next();
});
