// src/content/config.ts (или где ты объявляешь коллекции)
import { defineCollection, z } from "astro:content";

import { pb, urlWithPR } from "@/lib";

// Вспомогательно: оценка времени чтения (по числу слов)
function estimateReadingTime(html: string): number {
  const text = html
    .replace(/<[^>]*>/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  const words = text ? text.split(" ").length : 0;
  const minutes = Math.max(1, Math.round(words / 200)); // 200 wpm
  return minutes;
}

export const blogCollection = defineCollection({
  loader: async () => {
    if (!pb.authStore.isValid) {
      await pb
        .collection("_superusers")
        .authWithPassword(
          import.meta.env.PB_EMAIL,
          import.meta.env.PB_PASSWORD
        );
    }

    const posts = await pb.collection("blog").getFullList({
      filter: "published = true && blogI18n_via_post.status = 'published'",
      expand: "blogI18n_via_post",
      sort: "-created",
    });

    return posts.flatMap((post: any) => {
      const i18ns = (post.expand?.blogI18n_via_post ?? []) as any[];

      return i18ns.map((i18n) => {
        const slug: string = post.slug;
        const category: string = post.category;

        const locale: string = i18n.locale;

        const contentHtml: string = i18n.content ?? "";
        const coverUrl = post.cover
          ? urlWithPR(pb.files.getURL(post, post.cover))
          : null;

        return {
          id: `${locale}/${category}/${slug}`,
          locale,
          slug,
          category,
          meta: {
            title: i18n.data?.title,
            description: i18n.data?.description,
            image: i18n.data?.image,
            // SEO-JSON-LD можно собрать на странице
          },
          article: {
            coverUrl: coverUrl ?? null,
            datePublished: post.created ?? null,
            dateModified: post.updated ?? null,
            tags: post.tags ?? [],
            category: post.category ?? null,
            authors: post.authors ?? [], // если есть
            readingTimeMin: estimateReadingTime(contentHtml),
            // опциональные оверрайды OG из i18n:
            ogTitle: i18n.data?.ogTitle ?? null,
            ogDescription: i18n.data?.ogDescription ?? null,
          },
          contentHtml, // главное поле: HTML из PocketBase
        };
      });
    });
  },
  schema: z.object({
    locale: z.string(),
    slug: z.string(),
    category: z.string(),
    meta: z.object({
      title: z.string(),
      description: z.string().optional(),
      image: z.string().optional(),
    }),
    article: z.object({
      coverUrl: z.string().nullable(),
      datePublished: z.string().nullable(),
      dateModified: z.string().nullable(),
      tags: z.array(z.string()).default([]),
      category: z.string().nullable(),
      authors: z.array(z.string()).optional().default([]),
      readingTimeMin: z.number().int().min(1),
      ogTitle: z.string().nullable().optional(),
      ogDescription: z.string().nullable().optional(),
    }),
    contentHtml: z.string(), // HTML-строка из PB
  }),
});
