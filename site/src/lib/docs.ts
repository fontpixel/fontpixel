/** Routing and sidebar helpers for the tools/docs sections.
 *
 * Route shape: /{lang}/<section>/<slug>/, with an empty slug meaning the
 * section's index page.
 */
import { getCollection, type CollectionEntry } from 'astro:content';
import type { Lang } from '../i18n';

export type DocEntry = CollectionEntry<'docs'>;

/** Languages the docs body text actually exists in. Routes and hreflang are
 * emitted only for these — English-only content gets only /en/…; add a language
 * here when translations (e.g. *.zh.mdx) land. */
export const DOC_LANGS: Lang[] = ['en'];

export const DOC_SECTIONS = {
  'font-template': 'Font Template',
  'bdf-spec': 'BDF Specification',
  'bdfparser-js': 'bdfparser (JS/TS)',
  'bdfparser-py': 'bdfparser (Python)',
} as const;
export type DocSection = keyof typeof DOC_SECTIONS;

/** Slug within a section: strips the section prefix and a trailing index. Empty string for the index page. */
export function docSlug(entry: DocEntry, section: DocSection): string {
  const rest = entry.id.slice(section.length + 1);
  return rest.replace(/(^|\/)index$/, '').replace(/\/$/, '');
}

/** Page path without the language prefix (Base's path convention), with a trailing slash. */
export function docPath(section: DocSection, entry: DocEntry): string {
  const slug = docSlug(entry, section);
  return `/${section}/` + (slug ? `${slug}/` : '');
}

export async function sectionEntries(section: DocSection): Promise<DocEntry[]> {
  const entries = await getCollection('docs', ({ id }) => id.startsWith(`${section}/`));
  return entries.sort((a, b) => a.data.order - b.data.order);
}

/** Shared getStaticPaths implementation for all four sections. */
export async function docStaticPaths(section: DocSection) {
  const entries = await sectionEntries(section);
  return DOC_LANGS.flatMap((lang) =>
    entries.map((entry) => ({
      params: { lang, slug: docSlug(entry, section) || undefined },
      props: { entry },
    })),
  );
}
