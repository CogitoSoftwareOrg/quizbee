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
      // i18n: {
      //   defaultLocale: "en",
      //   locales: {
      //     en: "en",
      //     ru: "ru",
      //     es: "es",
      //     de: "de",
      //     fr: "fr",
      //     pt: "pt",
      //   },
      // },
    }),
  ],

  vite: {
    plugins: [tailwindcss()],
  },

  i18n: {
    locales: ["en", "ru", "es", "de", "fr", "pt"],
    defaultLocale: "en",
    routing: {
      prefixDefaultLocale: false,
      redirectToDefaultLocale: true,
    },
  },

  adapter: node({
    mode: "standalone",
  }),
});
