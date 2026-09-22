import type { APIRoute } from 'astro';
import { withBase } from '../lib/data';

export const GET: APIRoute = ({ site }) => new Response(
  `User-agent: *\nAllow: /\n\n# Binary packs and raw font metadata are not page content.\nDisallow: ${withBase('/data/packs/')}\nDisallow: ${withBase('/data/details/')}\n\nSitemap: ${new URL(withBase('/sitemap-index.xml'), site).href}\n`,
  { headers: { 'Content-Type': 'text/plain; charset=utf-8' } },
);
