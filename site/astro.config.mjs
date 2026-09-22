import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';
import { createReadStream, existsSync, statSync } from 'node:fs';

// Local dev/preview: vite's static handler serves .gz files with
// `Content-Encoding: gzip` and no Content-Type, so the browser transparently
// decompresses the BDF and renders it as text instead of downloading (and a
// "save as" would even write decompressed bytes under a .gz name). Serve
// /downloads/* ourselves with download headers. Production uses Pages
// with the equivalent headers in public/_headers.
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
// Production domain is fontpixel.com; override with OPF_SITE for special environments.
const site = process.env.OPF_SITE ?? 'https://fontpixel.com';

/**
 * Markdown/MDX links that point off-site open in a new tab and never hand the
 * target window a reference back (or a referrer). Written inline rather than
 * pulling in rehype-external-links for one rule.
 */
function rehypeExternalLinks() {
  const walk = (node) => {
    if (node.type === 'element' && node.tagName === 'a') {
      const href = node.properties?.href;
      if (typeof href === 'string' && /^https?:\/\//i.test(href)) {
        node.properties.target = '_blank';
        node.properties.rel = 'noopener noreferrer';
      }
    }
    for (const child of node.children ?? []) walk(child);
  };
  return (tree) => walk(tree);
}

// The layout supplies h1. Imported API references sometimes start at h4;
// preserve their nesting while removing skipped heading levels.
function rehypeHeadingOrder() {
  return (tree) => {
    const levels = [{ source: 0, output: 1 }];
    const walk = (node) => {
      if (node.type === 'element' && /^h[1-6]$/.test(node.tagName)) {
        const source = Number(node.tagName.slice(1));
        while (levels.length > 1 && levels.at(-1).source >= source) levels.pop();
        const output = Math.min(6, levels.at(-1).output + 1);
        node.tagName = `h${output}`;
        levels.push({ source, output });
      }
      for (const child of node.children ?? []) walk(child);
    };
    walk(tree);
  };
}

export default defineConfig({
  site,
  redirects: Object.fromEntries(
    ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr'].flatMap((lang) =>
      ['bitcount-single', 'bitcount-prop-single'].map((slug) => [
        `/${lang}/fonts/${slug}/`,
        { status: 301, destination: `/${lang}/fonts/bitcount/` },
      ]),
    ),
  ),
  integrations: [
    mdx(),
    svelte(),
    sitemap({
      filter: (page) => {
        const path = new URL(page).pathname.replace(process.env.OPF_BASE?.replace(/\/$/, '') || '', '');
        return path !== '/' && !/^\/404(?:\.html|\/)?$/.test(path)
          && !/\/fonts\/bitcount-(?:single|prop-single)\/?$/.test(path);
      },
      // The site has six parallel languages; each page lists the other five as
      // alternates, so search engines know they're different-language versions of the
      // same content, not duplicates
      i18n: {
        defaultLocale: 'zh',
        locales: { en: 'en', zh: 'zh-Hans', 'zh-Hant': 'zh-Hant',
                   ja: 'ja', ko: 'ko', fr: 'fr' },
      },
    }),
  ],
  // Cloudflare Pages serves from the domain root; override with OPF_BASE when deploying to a subpath
  base: process.env.OPF_BASE ?? '/',
  markdown: {
    rehypePlugins: [rehypeExternalLinks, rehypeHeadingOrder],
    shikiConfig: { theme: 'github-dark-high-contrast', langAlias: { markup: 'html' } },
  },
  vite: {
    plugins: [downloadsAsAttachments()],
    server: {
      // Font builds place thousands of immutable generated assets under public/data
      // and expose several thousand downloads through public/downloads. They are
      // build outputs, not HMR inputs; restart the dev server after `make fonts`
      // instead of watching them. Linux polling also keeps local development usable
      // when a desktop session has exhausted its per-user inotify-instance quota.
      watch: {
        usePolling: process.platform === 'linux',
        interval: 250,
        ignored: [
          '**/public/data/**',
          '**/public/downloads/**',
          '**/dist/**',
        ],
      },
    },
    resolve: {
      // MDX docs reference doc components via @dc/, avoiding relative paths that shift with directory depth
      alias: { '@dc': new URL('./src/components/docs', import.meta.url).pathname },
    },
  },
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
