// @ts-check
import { defineConfig } from "astro/config";

import node from "@astrojs/node";
import svelte from "@astrojs/svelte";
import sitemap from "@astrojs/sitemap";

import tailwindcss from "@tailwindcss/vite";

// https://astro.build/config
export default defineConfig({
  site: "https://quizbee.academy",

  integrations: [
    svelte(),
    sitemap({
      i18n: {
        defaultLocale: "en",
        locales: {
          en: "en",
          es: "es",
          ru: "ru",
          de: "de",
          fr: "fr",
          pt: "pt",
        },
      },
    }),
  ],

  vite: {
    plugins: [tailwindcss()],
    ssr: {
      noExternal: ["@cogisoft/ui-svelte-daisy"],
    },
  },

  i18n: {
    locales: ["en", "es", "ru", "de", "fr", "pt"],
    defaultLocale: "en",
    routing: {
      prefixDefaultLocale: true,
      redirectToDefaultLocale: true,
    },
  },

  adapter: node({
    mode: "standalone",
  }),
});
