import type { GetStaticPaths } from "astro";
import { pb } from "@/lib";
import { QuizesCategoryOptions } from "@/lib/pocketbase-types";
import { defaultLang, languages } from "@/i18n/ui";

type CatInfo = {
  name: string;
  count: number;
};

// ========================
// Helper Functions
// ========================

const sortByCreated = (a: any, b: any) => {
  const da = new Date(a.created ?? 0).getTime();
  const db = new Date(b.created ?? 0).getTime();
  return db - da;
};

const buildCategoryMap = (quizes: any[]): CatInfo[] => {
  const catMap = new Map<string, CatInfo>();
  for (const q of quizes) {
    const cat = q.category ?? "general";
    const meta = catMap.get(cat);
    if (!meta) {
      catMap.set(cat, {
        name: cat,
        count: 1,
      });
    } else {
      meta.count += 1;
    }
  }
  return Array.from(catMap.values()).sort((a, b) => b.count - a.count);
};

const fetchQuizes = async () => {
  const res = await pb.collection("quizes").getList(1, 1000, {
    filter: 'visibility = "search" && status = "final"',
    sort: "-created",
  });
  return res.items;
};

// ========================
// Non-localized Routes (e.g. /quizes)
// ========================

export const getStaticQuizPaths: GetStaticPaths = async ({ paginate }) => {
  const quizes = await fetchQuizes();
  const categories = buildCategoryMap(quizes);

  const pageSize = 20;
  quizes.sort(sortByCreated);

  return paginate(quizes, {
    pageSize,
    props: { categories },
  });
};

export const getStaticQuizCategoryPaths: GetStaticPaths = async ({
  paginate,
}) => {
  const categories = Object.values(QuizesCategoryOptions);
  const pageSize = 20;
  const paths: any[] = [];

  for (const category of categories) {
    const res = await pb.collection("quizes").getList(1, 1000, {
      filter: `category = "${category}" && visibility = "search" && status = "final"`,
      sort: "-created",
    });

    res.items.sort(sortByCreated);

    paths.push(
      ...paginate(res.items, {
        pageSize,
        params: { category },
        props: { category },
      })
    );
  }

  return paths;
};

// ========================
// Localized Routes (e.g. /[locale]/quizes)
// ========================

export const getStaticQuizLocalePaths: GetStaticPaths = async ({
  paginate,
}) => {
  const quizes = await fetchQuizes();
  const categories = buildCategoryMap(quizes);

  const pageSize = 20;
  const paths: any[] = [];

  quizes.sort(sortByCreated);

  for (const language in languages) {
    paths.push(
      ...paginate(quizes, {
        pageSize,
        params: { locale: language },
        props: { categories },
      })
    );
  }

  return paths;
};

export const getStaticQuizCategoryLocalePaths: GetStaticPaths = async ({
  paginate,
}) => {
  const categories = Object.values(QuizesCategoryOptions);
  const pageSize = 20;
  const paths: any[] = [];

  for (const category of categories) {
    const res = await pb.collection("quizes").getList(1, 1000, {
      filter: `category = "${category}" && visibility = "search" && status = "final"`,
      sort: "-created",
    });

    res.items.sort(sortByCreated);

    for (const language in languages) {
      paths.push(
        ...paginate(res.items, {
          pageSize,
          params: { locale: language, category },
          props: { category },
        })
      );
    }
  }

  return paths;
};
