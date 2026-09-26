/** Pure filter functions for the catalog page (contract per plan Task 16). */

import type { FamilyIndex } from './schema';
import { ratingOrder } from './rating';

export const SORTS = ['rating', 'rating-reverse', 'name', 'name-reverse', 'size', 'size-reverse', 'glyphs', 'glyphs-reverse'] as const;
export type SortKey = typeof SORTS[number];

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
    sort: 'rating',
  };
}

/** Whether a family (or one of its variants, when given) has every character. */
export type CharLookup = (slug: string, chars: string, variantId?: string) => boolean;
/** A multi-variant family's per-variant coverage ratios, aligned with charsetIds;
 *  undefined means the family's own ratios apply (a single variant). */
export type VariantCoverageLookup = (slug: string, variantId: string) => readonly number[] | undefined;

/** Lazily loaded per-variant data. Until one arrives, its filter is not applied. */
export interface VariantLookups {
  chars?: CharLookup;
  coverage?: VariantCoverageLookup;
}

type Variant = FamilyIndex['variants'][number];

function intersects<T>(a: T[], b: T[]): boolean {
  return a.some((x) => b.includes(x));
}

function charsOf(s: FilterState): string {
  return [...s.chars].filter((c) => !/\s/.test(c)).join('');
}

/** Whether any filter that a single variant has to satisfy is active. */
export function hasVariantFilters(s: FilterState): boolean {
  return Boolean(s.sizes.length || s.inkH || s.scripts.length || s.spacing.length
    || s.weights.length || s.coverage.length || charsOf(s));
}

/** Whether the lookups needed to judge the active variant filters have loaded. */
export function variantLookupsReady(s: FilterState, lookups: VariantLookups): boolean {
  return (!charsOf(s) || Boolean(lookups.chars)) && (!s.coverage.length || Boolean(lookups.coverage));
}

/**
 * The variants that meet every active per-variant filter at once. A family
 * counts as a match only through one such variant: a size from one file and a
 * script from another would describe a font that doesn't exist.
 */
export function matchingVariants(
  f: FamilyIndex,
  s: FilterState,
  lookups: VariantLookups = {},
  charsetIds: readonly string[] = [],
): Variant[] {
  const chars = charsOf(s);
  const coverageReqs = s.coverage.map((req) => ({ ...req, index: charsetIds.indexOf(req.id) }));
  return f.variants.filter((v) => {
    if (s.sizes.length && !s.sizes.includes(v.size)) return false;
    if (s.inkH && !(v.inkHeight >= s.inkH[0] && v.inkHeight <= s.inkH[1])) return false;
    // The family label merges its variants (a complete variant hides the
    // partial tier), so the script must be both the family's and this variant's.
    if (s.scripts.length && !s.scripts.some((sc) => f.scripts.includes(sc) && v.scripts.includes(sc)))
      return false;
    if (s.spacing.length && !s.spacing.includes(v.spacing)) return false;
    if (s.weights.length && !s.weights.includes(v.weight)) return false;
    if (coverageReqs.length) {
      // Until the per-variant file loads, every variant is judged by the
      // family's best ratios, as the index records them.
      const ratios = (f.variants.length > 1 ? lookups.coverage?.(f.slug, v.id) : undefined) ?? f.coverage;
      for (const req of coverageReqs) {
        const got = req.index === -1 ? (f.coverageSummary[req.id] ?? 0) : (ratios[req.index] ?? 0);
        if (got < req.min) return false;
      }
    }
    if (chars && lookups.chars && !lookups.chars(f.slug, chars, v.id)) return false;
    return true;
  });
}

export function applyFilters(
  fams: FamilyIndex[],
  s: FilterState,
  lookups: VariantLookups = {},
  charsetIds?: string[],
): FamilyIndex[] {
  // Split on whitespace into terms and require every term to hit: matching
  // the whole query as one substring would never find a cross-field
  // combination like "俐方 cubic" — each word exists somewhere, but never
  // joined together in any single piece of text
  const terms = s.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const perVariant = hasVariantFilters(s);
  let out = fams.filter((f) => {
    if (terms.length) {
      // searchText is generated at build time and already expands the family name across Simplified/Traditional variants
      const hay = `${f.searchText} ${f.name} ${Object.values(f.names).join(' ')} ${f.authors.join(' ')} ${f.slug}`.toLowerCase();
      if (!terms.every((t) => hay.includes(t))) return false;
    }
    if (s.forms.length && !intersects(s.forms, f.forms)) return false;
    if (s.vibes.length && !intersects(s.vibes, f.vibes)) return false;
    if (s.licenses.length) {
      const lic = f.license.spdx ?? 'unknown';
      if (!s.licenses.includes(lic)) return false;
    }
    // Size, ink height, script, spacing, weight, coverage and characters must
    // all hold for one and the same variant.
    if (perVariant && !matchingVariants(f, s, lookups, charsetIds).length) return false;
    return true;
  });

  // Keeping the original semantics: sort by the Chinese name when present,
  // otherwise by the Latin name. Sorting is independent of the UI language,
  // so it sorts by Chinese name even in the English UI — this behavior
  // predates the addition of multi-language names.
  const byName = (f: FamilyIndex) => (f.names['zh-Hans'] || f.name).toLowerCase();
  out = [...out];
  const reversed = s.sort.endsWith('-reverse');
  const order = s.sort.replace(/-reverse$/, '');
  switch (order) {
    case 'rating':
      out = ratingOrder(out, charsetIds);
      break;
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
  return reversed ? out.reverse() : out;
}
