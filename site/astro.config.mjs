import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

export default defineConfig({
  integrations: [svelte()],
  base: process.env.PFC_BASE ?? '/pixel-font-collection',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
