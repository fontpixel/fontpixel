import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { DOC_SECTIONS, docPath, type DocSection } from '../lib/docs';
import { LANGS, LANG_NAMES } from '../i18n';
import { withBase } from '../lib/data';

export const GET: APIRoute = async ({ site }) => {
  const url = (path: string) => new URL(withBase(path), site).href;
  const docs = (await getCollection('docs')).sort((a, b) => a.id.localeCompare(b.id));
  const text = [
    '# FontPixel', '',
    '> A collection of freely licensed pixel and bitmap fonts, with font previews, downloads, character coverage reports, and bitmap font tooling documentation.', '',
    'Font pages describe the font family, authors, provenance, available sizes, character coverage, and its own license. The MIT license covers the site code, not every font. Follow each font’s license and attribution requirements.', '',
    'The catalogue and font pages are statically rendered. Search and comparison run in the browser. Documentation is in English; the catalogue is available in six languages.', '',
    '## Catalogue', '',
    ...LANGS.map((lang) => `- [${LANG_NAMES[lang]} catalogue](${url(`/${lang}/`)}): Browse fonts and follow static pagination to individual family pages.`),
    `- [About and inclusion criteria](${url('/en/about/')}): Licensing policy, font metrics, coverage data sources, and methodology.`,
    `- [Font comparison](${url('/en/compare/')}): Compare pixel font samples in the browser.`,
    `- [Sitemap](${url('/sitemap-index.xml')}): Index of canonical page URLs, including every font family.`, '',
    '## Documentation', '',
    ...docs.map((entry) => {
      const section = entry.id.split('/')[0] as DocSection;
      return `- [${entry.data.title} — ${DOC_SECTIONS[section]}](${url(`/en${docPath(section, entry)}index.md`)}): ${entry.data.description}`;
    }), '',
    '## Optional', '',
    '- [Source repository](https://github.com/fontpixel/fontpixel): Build pipeline, font metadata, and contribution instructions.',
    '- [English README](https://github.com/fontpixel/fontpixel/blob/main/README.md): Local setup and architecture.',
    '- [中文说明](https://github.com/fontpixel/fontpixel/blob/main/README.zh.md): Chinese project documentation.', '',
  ].join('\n');
  return new Response(text, { headers: { 'Content-Type': 'text/plain; charset=utf-8' } });
};
