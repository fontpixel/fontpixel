import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';

// Production domain. canonical, og:url, and sitemap all need absolute URLs for search
// engines to honor them.
// Production domain is pixelfonts.dev; override with OPF_SITE for special environments.
const site = process.env.OPF_SITE ?? 'https://pixelfonts.dev';

export default defineConfig({
  site,
  integrations: [
    mdx(),
    svelte(),
    sitemap({
      // The site has six parallel languages; each page lists the other five as
      // alternates, so search engines know they're different-language versions of the
      // same content, not duplicates
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', zh: 'zh-Hans', 'zh-Hant': 'zh-Hant',
                   ja: 'ja', ko: 'ko', fr: 'fr' },
      },
    }),
  ],
  // Cloudflare Pages serves from the domain root; override with OPF_BASE when deploying to a subpath
  base: process.env.OPF_BASE ?? '/',
  vite: {
    resolve: {
      // MDX docs reference doc components via @dc/, avoiding relative paths that shift with directory depth
      alias: { '@dc': new URL('./src/components/docs', import.meta.url).pathname },
    },
  },
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
