import type { GetStaticPaths } from "astro";
import { getCollection } from "astro:content";

import { defaultLang } from "@/i18n/ui";

type CatInfo = {
  name: string;
  count: number;
  cover?: string | null;
  description?: string | null;
};

// ========================
// Helper Functions
// ========================

const sortByDate = (a: any, b: any) => {
  const da = new Date(
    a.data.article?.datePublished ?? a.data.article?.dateModified ?? 0
  ).getTime();
  const db = new Date(
    b.data.article?.datePublished ?? b.data.article?.dateModified ?? 0
  ).getTime();
  return db - da;
};

const buildCategoryMap = (posts: any[]): CatInfo[] => {
  const catMap = new Map<string, CatInfo>();
  for (const p of posts) {
    const cat = p.data.category ?? "general";
    const meta = catMap.get(cat);
    if (!meta) {
      catMap.set(cat, {
        name: cat,
        count: 1,
        cover: p.data.article?.coverUrl ?? null,
        description: p.data.meta?.description ?? null,
      });
    } else {
      meta.count += 1;
    }
  }
  return Array.from(catMap.values()).sort((a, b) => b.count - a.count);
};

const filterByLocale = async (
  onlyDefaultLang: boolean
): Promise<Map<string, any[]>> => {
  const all = await getCollection("blogPb", (post) => {
    // ID format: ${locale}/${category}/${slug}
    // Extract locale from ID (first part before /)
    const postLocale = post.id.split("/")[0];
    return onlyDefaultLang ? postLocale === defaultLang : true;
  });

  const byLocale = new Map<string, any[]>();
  for (const p of all) {
    const loc = p.data.locale;
    if (!byLocale.has(loc)) byLocale.set(loc, []);
    byLocale.get(loc)!.push(p);
  }

  return byLocale;
};

export const getStaticBlogPaths: GetStaticPaths = async ({ paginate }) => {
  const byLocale = await filterByLocale(true);

  const pageSize = 12;
  const paths: any[] = [];

  for (const [locale, list] of byLocale.entries()) {
    list.sort(sortByDate);
    const categories = buildCategoryMap(list);

    paths.push(
      ...paginate(list, {
        pageSize,
        params: { locale },
        props: { locale, categories },
      })
    );
  }

  return paths;
};

export const getStaticBlogCategoryPaths: GetStaticPaths = async ({
  paginate,
}) => {
  const byLocale = await filterByLocale(true);

  const pageSize = 12;
  const paths: any[] = [];

  for (const [locale, posts] of byLocale.entries()) {
    const byCat = new Map<string, any[]>();
    for (const p of posts) {
      const cat = p.data.category ?? "general";
      if (!byCat.has(cat)) byCat.set(cat, []);
      byCat.get(cat)!.push(p);
    }

    for (const [category, list] of byCat.entries()) {
      list.sort(sortByDate);

      paths.push(
        ...paginate(list, {
          pageSize,
          params: { locale, category },
          props: { category, locale },
        })
      );
    }
  }

  return paths;
};

const buildPostPaths = (groups: Map<string, any[]>) => {
  const paths: any[] = [];

  for (const [, list] of groups) {
    list.sort(sortByDate);

    for (let i = 0; i < list.length; i++) {
      const cur = list[i];
      const prev = i > 0 ? list[i - 1] : null;
      const next = i < list.length - 1 ? list[i + 1] : null;

      paths.push({
        params: {
          locale: cur.data.locale,
          category: cur.data.category,
          slug: cur.data.slug,
        },
        props: {
          meta: cur.data.meta,
          content: cur.data.contentHtml,
          article: cur.data.article,
          toc: cur.data.toc ?? null,
          previousPost: prev
            ? {
                locale: prev.data.locale,
                category: prev.data.category,
                slug: prev.data.slug,
                title: prev.data.meta?.title,
              }
            : null,
          nextPost: next
            ? {
                locale: next.data.locale,
                category: next.data.category,
                slug: next.data.slug,
                title: next.data.meta?.title,
              }
            : null,
        },
      });
    }
  }

  return paths;
};

export const getStaticBlogPostPaths: GetStaticPaths = async () => {
  const byLocale = await filterByLocale(true);

  const groups = new Map<string, any[]>();
  for (const [, posts] of byLocale.entries()) {
    for (const p of posts) {
      const key = `${p.data.locale}:${p.data.category}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(p);
    }
  }

  return buildPostPaths(groups);
};

// ========================
// Localized Routes (e.g. /[locale]/blog)
// ========================

export const getStaticBlogLocalePaths: GetStaticPaths = async ({
  paginate,
}) => {
  const byLocale = await filterByLocale(false);

  const pageSize = 12;
  const paths: any[] = [];

  for (const [locale, list] of byLocale.entries()) {
    list.sort(sortByDate);
    const categories = buildCategoryMap(list);

    paths.push(
      ...paginate(list, {
        pageSize,
        params: { locale },
        props: { locale, categories },
      })
    );
  }

  return paths;
};

export const getStaticBlogCategoryLocalePaths: GetStaticPaths = async ({
  paginate,
}) => {
  const byLocale = await filterByLocale(false);

  const pageSize = 12;
  const paths: any[] = [];

  for (const [locale, posts] of byLocale.entries()) {
    const byCat = new Map<string, any[]>();
    for (const p of posts) {
      const cat = p.data.category ?? "general";
      if (!byCat.has(cat)) byCat.set(cat, []);
      byCat.get(cat)!.push(p);
    }

    for (const [category, list] of byCat.entries()) {
      list.sort(sortByDate);

      paths.push(
        ...paginate(list, {
          pageSize,
          params: { locale, category },
          props: { category, locale },
        })
      );
    }
  }

  return paths;
};

export const getStaticBlogPostLocalePaths: GetStaticPaths = async () => {
  const byLocale = await filterByLocale(false);

  const groups = new Map<string, any[]>();
  for (const [, posts] of byLocale.entries()) {
    for (const p of posts) {
      const key = `${p.data.locale}:${p.data.category}`;
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(p);
    }
  }

  return buildPostPaths(groups);
};
