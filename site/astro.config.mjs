import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

export default defineConfig({
  integrations: [svelte()],
  base: process.env.FBF_BASE ?? '/foss-bitmap-fonts',
  trailingSlash: 'ignore',
  build: { format: 'directory' },
});
