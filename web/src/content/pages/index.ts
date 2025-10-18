import { defineCollection, z } from "astro:content";

export const pagesCollection = defineCollection({
  type: "data",
  schema: z.object({
    title: z.string(),
    lastUpdated: z.string(),
    sections: z.array(
      z.object({
        heading: z.string(),
        content: z.string(),
        subsections: z
          .array(
            z.object({
              subheading: z.string(),
              content: z.string(),
            })
          )
          .optional(),
      })
    ),
  }),
});
