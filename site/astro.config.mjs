import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';
import { createReadStream, existsSync, statSync } from 'node:fs';

// Local dev/preview: vite's static handler serves .gz files with
// `Content-Encoding: gzip` and no Content-Type, so the browser transparently
// decompresses the BDF and renders it as text instead of downloading (and a
// "save as" would even write decompressed bytes under a .gz name). Serve
// /downloads/* ourselves with download headers. Production goes through R2,
// where the sync script already sets proper content types.
const DOWNLOADS_DIR = new URL('./public/downloads/', import.meta.url).pathname;
const DOWNLOAD_TYPES = { '.gz': 'application/gzip', '.zip': 'application/zip', '.ttf': 'font/ttf' };
function downloadsAsAttachments() {
  const handler = (req, res, next) => {
    const m = /^\/downloads\/([^/?#]+)/.exec(req.url ?? '');
    if (!m) return next();
    const name = decodeURIComponent(m[1]);
    const file = DOWNLOADS_DIR + name;
    if (name.includes('..') || name.includes('/') || !existsSync(file)) return next();
    const ext = name.slice(name.lastIndexOf('.'));
    res.setHeader('Content-Type', DOWNLOAD_TYPES[ext] ?? 'application/octet-stream');
    res.setHeader('Content-Disposition', `attachment; filename="${name}"`);
    res.setHeader('Content-Length', statSync(file).size);
    createReadStream(file).pipe(res);
  };
  return {
    name: 'opf-downloads-as-attachments',
    configureServer(server) {
      server.middlewares.use(handler);
    },
    configurePreviewServer(server) {
      server.middlewares.use(handler);
    },
  };
}

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
    plugins: [downloadsAsAttachments()],
    resolve: {
      // MDX docs reference doc components via @dc/, avoiding relative paths that shift with directory depth
      alias: { '@dc': new URL('./src/components/docs', import.meta.url).pathname },
    },
  },
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
