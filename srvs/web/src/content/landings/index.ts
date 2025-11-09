import { defineCollection, z } from "astro:content";

import { setByPath } from "@quizbee/ui-astro";

import { pb } from "@/lib";

const LandingSchema = z.object({
  locale: z.string(),
  slug: z.string(),
  meta: z.object({
    active: z.string().optional(),
    headerCtaHref: z.string().optional(),
    structuredData: z.record(z.string(), z.any()).optional(),
    title: z.string(),
    description: z.string().optional(),
    image: z.string().optional(),
  }),
  sections: z.array(
    z.object({
      type: z.enum([
        "Hero",
        "Pains",
        "Features",
        "HowItWorks",
        "Products",
        "Testimonials",
        "Pricing",
        "FAQ",
        "CTA",
      ]),
      props: z.any(), // можно детализировать по типам секций, если хочешь
    })
  ),
});

export const landingsCollectionPb = defineCollection({
  loader: async () => {
    if (!pb.authStore.isValid) {
      await pb
        .collection("_superusers")
        .authWithPassword(
          import.meta.env.PB_EMAIL,
          import.meta.env.PB_PASSWORD
        );
    }

    const pages = await pb.collection("landings").getFullList({
      filter:
        "published = true && landingsI18n_via_landing.status = 'published'",
      expand: "landingsI18n_via_landing",
      sort: "-updated",
    });

    return pages.flatMap((page) => {
      const i18ns = page.expand?.landingsI18n_via_landing;
      return i18ns.map((i18n: any) => {
        return {
          id: `${i18n.locale}/${page.slug}`,
          locale: i18n.locale,
          slug: page.slug,
          meta: {
            ...page.meta,
            title: i18n.data.title,
            description: i18n.data.description,
            image: i18n.data.image,
          },
          sections: page.structure.map((s: any) => {
            const props = structuredClone(s.props ?? {});
            const i18nMap = s.i18nKeys ?? {};

            for (const path in i18nMap) {
              const key = i18nMap[path];
              if (!key) continue;
              const translation = i18n.data[key];
              if (translation !== undefined)
                setByPath(props, path, translation);
            }

            return { type: s.type, props };
          }),
        };
      });
    });
  },
  schema: LandingSchema,
});

export const landingsCollection = defineCollection({
  type: "data",
  schema: LandingSchema,
});
