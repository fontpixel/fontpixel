/** Pure filter functions for the catalog page (contract per plan Task 16). */

import type { FamilyIndex } from './schema';

export type SortKey = 'name' | 'size' | 'glyphs';

export interface CoverageReq {
  id: string;
  min: number;
}

export interface FilterState {
  q: string;
  forms: string[];
  vibes: string[];
  sizes: number[];
  inkH: [number, number] | null;
  scripts: string[];
  licenses: string[];
  spacing: string[];
  weights: string[];
  coverage: CoverageReq[];
  chars: string;
  sort: SortKey;
}

export function emptyState(): FilterState {
  return {
    q: '',
    forms: [],
    vibes: [],
    sizes: [],
    inkH: null,
    scripts: [],
    licenses: [],
    spacing: [],
    weights: [],
    coverage: [],
    chars: '',
    sort: 'name',
  };
}

export type CharLookup = (slug: string, chars: string) => boolean;

function intersects<T>(a: T[], b: T[]): boolean {
  return a.some((x) => b.includes(x));
}

export function applyFilters(
  fams: FamilyIndex[],
  s: FilterState,
  charLookup?: CharLookup,
  charsetIds?: string[],
): FamilyIndex[] {
  const idxOf = new Map((charsetIds ?? []).map((id, i) => [id, i]));
  // Split on whitespace into terms and require every term to hit: matching
  // the whole query as one substring would never find a cross-field
  // combination like "俐方 cubic" — each word exists somewhere, but never
  // joined together in any single piece of text
  const terms = s.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const chars = [...s.chars].filter((c) => !/\s/.test(c)).join('');
  let out = fams.filter((f) => {
    if (terms.length) {
      // searchText is generated at build time and already expands the family name across Simplified/Traditional variants
      const hay = `${f.searchText} ${f.name} ${Object.values(f.names).join(' ')} ${f.authors.join(' ')} ${f.slug}`.toLowerCase();
      if (!terms.every((t) => hay.includes(t))) return false;
    }
    if (s.forms.length && !s.forms.includes(f.form)) return false;
    if (s.vibes.length && !intersects(s.vibes, f.vibes)) return false;
    if (s.sizes.length && !intersects(s.sizes, f.sizes)) return false;
    // A match if any variant's ink height falls in the range: comparing the
    // family by its max value alone would make WenQuanYi (11/12/13/14/16)
    // miss a 14-14 filter
    if (s.inkH && !f.inkHeights.some((h) => h >= s.inkH![0] && h <= s.inkH![1]))
      return false;
    if (s.scripts.length && !intersects(s.scripts, f.scripts)) return false;
    if (s.licenses.length) {
      const lic = f.license.spdx ?? 'unknown';
      if (!s.licenses.includes(lic)) return false;
    }
    if (s.spacing.length && !intersects(s.spacing, f.spacing)) return false;
    if (s.weights.length && !intersects(s.weights, f.weights)) return false;
    for (const req of s.coverage) {
      const i = idxOf.get(req.id);
      const got = i === undefined
        ? (f.coverageSummary[req.id] ?? 0)
        : (f.coverage[i] ?? 0);
      if (got < req.min) return false;
    }
    if (chars && charLookup && !charLookup(f.slug, chars)) return false;
    return true;
  });

  // Keeping the original semantics: sort by the Chinese name when present,
  // otherwise by the Latin name. Sorting is independent of the UI language,
  // so it sorts by Chinese name even in the English UI — this behavior
  // predates the addition of multi-language names.
  const byName = (f: FamilyIndex) => (f.names['zh-Hans'] || f.name).toLowerCase();
  out = [...out];
  switch (s.sort) {
    case 'name':
      out.sort((a, b) => byName(a).localeCompare(byName(b)));
      break;
    case 'size':
      out.sort((a, b) => Math.min(...a.sizes) - Math.min(...b.sizes));
      break;
    case 'glyphs':
      out.sort((a, b) => b.glyphCount - a.glyphCount);
      break;
  }
  return out;
}
