/** 目录页筛选纯函数（契约见计划 Task 16）。 */

import type { FamilyIndex } from './schema';

export type SortKey = 'name' | 'size' | 'glyphs' | 'added';

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
  commercialOnly: boolean;
  spacing: string[];
  weights: string[];
  origin: 'all' | 'native' | 'converted';
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
    commercialOnly: false,
    spacing: [],
    weights: [],
    origin: 'all',
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
): FamilyIndex[] {
  const q = s.q.trim().toLowerCase();
  const chars = [...s.chars].filter((c) => !/\s/.test(c)).join('');
  let out = fams.filter((f) => {
    if (q) {
      const hay = `${f.name} ${f.nameZh} ${f.author} ${f.slug} ${f.vibes.join(' ')}`
        .toLowerCase();
      if (!hay.includes(q)) return false;
    }
    if (s.forms.length && !s.forms.includes(f.form)) return false;
    if (s.vibes.length && !intersects(s.vibes, f.vibes)) return false;
    if (s.sizes.length && !intersects(s.sizes, f.sizes)) return false;
    if (s.inkH && (f.inkHeight < s.inkH[0] || f.inkHeight > s.inkH[1])) return false;
    if (s.scripts.length && !intersects(s.scripts, f.scripts)) return false;
    if (s.licenses.length) {
      const lic = f.license.spdx ?? 'unknown';
      if (!s.licenses.includes(lic)) return false;
    }
    if (s.commercialOnly && f.license.commercial !== true) return false;
    if (s.spacing.length && !intersects(s.spacing, f.spacing)) return false;
    if (s.weights.length && !intersects(s.weights, f.weights)) return false;
    if (s.origin === 'native' && f.converted) return false;
    if (s.origin === 'converted' && !f.converted) return false;
    for (const req of s.coverage) {
      if ((f.coverageSummary[req.id] ?? 0) < req.min) return false;
    }
    if (chars && charLookup && !charLookup(f.slug, chars)) return false;
    return true;
  });

  const byName = (f: FamilyIndex) => (f.nameZh || f.name).toLowerCase();
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
    case 'added':
      out.sort((a, b) => (b.added || '').localeCompare(a.added || ''));
      break;
  }
  return out;
}
