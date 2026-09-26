/** Sidebar trees of the tools/docs sections, grouped like the original
 * font.tomchen.org (Docusaurus) sidebars. A page is named by its slug within
 * the section ('' is the section's index page); its label defaults to the
 * page's frontmatter `label`. The tree also sets the pager's page order.
 */
import type { DocSection } from './docs';

export type SidebarNode = SidebarPage | SidebarCategory;
export interface SidebarPage {
  slug: string;
  /** Overrides the frontmatter label, e.g. a short name inside a category */
  label?: string;
}
export interface SidebarCategory {
  category: string;
  /** Starts folded unless it holds the current page */
  collapsed?: boolean;
  items: SidebarNode[];
}

const pages = (...slugs: string[]): SidebarPage[] => slugs.map((slug) => ({ slug }));
const named = (prefix: string, entries: [string, string][]): SidebarPage[] =>
  entries.map(([slug, label]) => ({ slug: `${prefix}${slug}`, label }));

export const DOC_SIDEBARS: Record<DocSection, SidebarNode[]> = {
  'bdfparser-js': [
    ...pages('', 'editor'),
    { category: 'BDF Parser (TS/JS) API', items: pages('font', 'glyph', 'bitmap') },
    {
      category: 'API TS Doc (auto-generated)',
      collapsed: true,
      items: [
        { slug: 'api', label: 'Table of contents' },
        {
          category: 'Classes',
          collapsed: true,
          items: named('api/classes/', [
            ['bitmap', 'Bitmap'],
            ['font', 'Font'],
            ['glyph', 'Glyph'],
          ]),
        },
        {
          category: 'Type aliases',
          collapsed: true,
          items: named('api/types/', [
            ['codepointrangetype', 'CodepointRangeType'],
            ['directionnumbertype', 'DirectionNumberType'],
            ['directiontype', 'DirectionType'],
            ['glyphdrawmodetype', 'GlyphDrawModeType'],
            ['glyphmeta', 'GlyphMeta'],
            ['glyphmetainfont', 'GlyphMetaInFont'],
            ['headers', 'Headers'],
            ['ordertype', 'OrderType'],
            ['props', 'Props'],
            ['todatafuncrettype', 'TodataFuncRetType'],
          ]),
        },
        {
          category: 'Functions',
          collapsed: true,
          items: named('api/functions/', [
            ['bitmap', '$Bitmap'],
            ['font', '$Font'],
            ['glyph', '$Glyph'],
          ]),
        },
      ],
    },
  ],
  'bdfparser-py': [
    ...pages(''),
    { category: 'BDF Parser (Python) API', items: pages('font', 'glyph', 'bitmap') },
  ],
  'bdf-spec': [
    ...pages('', 'intro', 'tape_format'),
    {
      category: 'File Format',
      items: pages('file_format', 'file_format/global_font_info', 'file_format/individual_glyph_info'),
    },
    ...pages('examples', 'spec_2.1', 'bdf_properties'),
  ],
  'font-template': pages(''),
};

/** Every page slug of a tree, in reading order. */
export function sidebarSlugs(nodes: SidebarNode[]): string[] {
  return nodes.flatMap((n) => ('slug' in n ? [n.slug] : sidebarSlugs(n.items)));
}

/** Whether a category is unfolded: when it isn't collapsed by default, or holds the current page. */
export function categoryOpen(category: SidebarCategory, current: string): boolean {
  return !category.collapsed || sidebarSlugs(category.items).includes(current);
}
