import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import svelte from '@astrojs/svelte';
import sitemap from '@astrojs/sitemap';

// 生产域名。canonical、og:url、sitemap 都要绝对地址，搜索引擎才认。
// 生产域名 pixelfonts.dev；特殊环境可用 OPF_SITE 覆盖。
const site = process.env.OPF_SITE ?? 'https://pixelfonts.dev';

export default defineConfig({
  site,
  integrations: [
    mdx(),
    svelte(),
    sitemap({
      // 站点是六语并列的，每个页面把其余五种语言列为 alternate，
      // 搜索引擎才知道它们是同一内容的不同语言版，而不是重复内容
      i18n: {
        defaultLocale: 'en',
        locales: { en: 'en', zh: 'zh-Hans', 'zh-Hant': 'zh-Hant',
                   ja: 'ja', ko: 'ko', fr: 'fr' },
      },
    }),
  ],
  // Cloudflare Pages 服务在域名根目录；要部署到子路径时用 OPF_BASE 覆盖
  base: process.env.OPF_BASE ?? '/',
  vite: {
    resolve: {
      // MDX 文档里用 @dc/ 引文档组件，免去随目录深度变化的相对路径
      alias: { '@dc': new URL('./src/components/docs', import.meta.url).pathname },
    },
  },
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
