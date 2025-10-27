// @ts-check
import { defineConfig } from "astro/config";

import node from "@astrojs/node";
import svelte from "@astrojs/svelte";
import sitemap from "@astrojs/sitemap";

import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  site: "https://quizbee.academy",

  image: {
    remotePatterns: [
      {
        protocol: "http",
        hostname: "pb",
        port: "8090",
        pathname: "/api/files/**",
      },
      {
        protocol: "https",
        hostname: "*.quizbee.academy",
        pathname: "/api/files/**",
      },
    ],
  },

  integrations: [
    svelte(),
    sitemap({
      i18n: {
        defaultLocale: "en",
        locales: {
          en: "en",
          es: "es",
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
    envDir: "../../envs",
  },

  i18n: {
    locales: ["en", "es", "de", "fr", "pt"],
    defaultLocale: "en",
    routing: {
      prefixDefaultLocale: false,
      redirectToDefaultLocale: false,
    },
  },

  adapter: node({
    mode: "standalone",
  }),
});
