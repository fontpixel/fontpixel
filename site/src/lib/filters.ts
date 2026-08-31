/** 目录页筛选纯函数（契约见计划 Task 16）。 */

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
  // 按空白拆词，全部命中才算：整串当子串匹配的话，「俐方 cubic」这种
  // 跨字段的组合永远搜不到——两个词分别都在，连起来却不是任何一段文本
  const terms = s.q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const chars = [...s.chars].filter((c) => !/\s/.test(c)).join('');
  let out = fams.filter((f) => {
    if (terms.length) {
      // searchText 由构建期生成，已把家族名做过简繁异体展开
      const hay = `${f.searchText} ${f.name} ${Object.values(f.names).join(' ')} ${f.authors.join(' ')} ${f.slug}`.toLowerCase();
      if (!terms.every((t) => hay.includes(t))) return false;
    }
    if (s.forms.length && !s.forms.includes(f.form)) return false;
    if (s.vibes.length && !intersects(s.vibes, f.vibes)) return false;
    if (s.sizes.length && !intersects(s.sizes, f.sizes)) return false;
    // 任一变体的墨迹高度落在区间即命中：家族只按最大值比的话，
    // 文泉驿（11/12/13/14/16）按 14-14 筛就落空了
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

  // 沿用原有语义：有中文名就按中文名排，否则按拉丁名。排序与界面语言无关，
  // 所以英文界面下也是按中文名排的——这是加多语言名之前就有的行为。
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
