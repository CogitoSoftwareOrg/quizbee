// src/content/config.ts (или где ты объявляешь коллекции)
import { defineCollection, z } from "astro:content";

import { pb, pbPublic, urlWithPR } from "@/lib";

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

export type TocItem = { id: string; text: string; level: 2 | 3 };
export function buildTocFromHtml(html: string): TocItem[] {
  const re = /<(h[23])\s+[^>]*id="([^"]+)"[^>]*>(.*?)<\/h[23]>/gi;
  const items: TocItem[] = [];
  let m;
  while ((m = re.exec(html))) {
    const level = m[1] === "h2" ? 2 : 3;
    const id = m[2];
    const text = m[3].replace(/<[^>]+>/g, "").trim();
    items.push({ id, text, level });
  }
  return items;
}

function slugify(text: string) {
  return text
    .toLowerCase()
    .replace(/<\/?[^>]+(>|$)/g, "")
    .replace(/[^\p{L}\p{N}\s-]/gu, "")
    .trim()
    .replace(/\s+/g, "-")
    .slice(0, 64);
}

// Добавляет id в h2/h3, если их нет
export function ensureHeadingIds(html: string): string {
  return html.replace(
    /<(h[23])([^>]*)>(.*?)<\/\1>/gi,
    (m, tag, attrs, inner) => {
      // уже есть id?
      const hasId = /\sid="/i.test(attrs);
      if (hasId) return m;
      // текст без тегов
      const plain = inner.replace(/<[^>]+>/g, "").trim();
      const id = slugify(plain) || crypto.randomUUID();
      // аккуратно вставляем id в открывающий тег
      const attrsClean = attrs.trim();
      const space = attrsClean.length ? " " : "";
      return `<${tag}${space}${attrsClean} id="${id}">${inner}</${tag}>`;
    }
  );
}

export const blogCollectionPb = defineCollection({
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
        const slug = post.slug;
        const category = post.category;

        const locale = i18n.locale;

        const rawHtml = i18n.content ?? "";
        const contentHtml = ensureHeadingIds(rawHtml);
        const toc = buildTocFromHtml(contentHtml);
        console.log("toc", toc);
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
          toc,
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
    toc: z.array(
      z.object({ id: z.string(), text: z.string(), level: z.number() })
    ),
  }),
});
