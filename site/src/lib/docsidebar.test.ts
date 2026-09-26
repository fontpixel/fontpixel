import { readdirSync } from 'node:fs';
import { expect, test } from 'vitest';
import { DOC_SIDEBARS, categoryOpen, sidebarSlugs, type SidebarCategory } from './docsidebar';

/** Page slugs of a section as the router derives them (docs.ts `docSlug`). */
function slugsOnDisk(section: string): string[] {
  return readdirSync(new URL(`../content/docs/${section}/`, import.meta.url), { recursive: true })
    .filter((p): p is string => typeof p === 'string' && /\.(md|mdx)$/.test(p))
    .map((p) => p.replace(/\.(md|mdx)$/, '').replace(/(^|\/)index$/, ''));
}

// A page left out of the tree would be missing from the sidebar and the pager.
test('every docs page appears in its section sidebar exactly once', () => {
  for (const [section, tree] of Object.entries(DOC_SIDEBARS)) {
    const slugs = sidebarSlugs(tree);
    expect(new Set(slugs).size, section).toBe(slugs.length);
    expect([...slugs].sort(), section).toEqual(slugsOnDisk(section).sort());
  }
});

test('a collapsed category unfolds only when it holds the current page', () => {
  const api = DOC_SIDEBARS['bdfparser-js'].find(
    (n): n is SidebarCategory => 'category' in n && n.category.startsWith('API TS Doc'),
  )!;
  expect(categoryOpen(api, '')).toBe(false);
  expect(categoryOpen(api, 'api/types/props')).toBe(true);
  expect(categoryOpen({ category: 'x', items: [] }, '')).toBe(true);
});
