import { defineCollection, z } from "astro:content";

export const pagesCollection = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    lastUpdated: z.string(),
  }),
});
