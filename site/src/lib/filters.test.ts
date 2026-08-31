import { describe, expect, test } from 'vitest';
import { applyFilters, emptyState, type FilterState } from './filters';
import { decodeState, encodeState } from './urlstate';
import type { FamilyIndex } from './schema';

function fam(over: Partial<FamilyIndex>): FamilyIndex {
  return {
    slug: 'x',
    name: 'X',
    names: { en: 'X' },
    authors: [],
    authorsEn: [],
    form: 'gothic',
    vibes: [],
    scripts: ['latin'],
    sizes: [12],
    weights: ['regular'],
    spacing: ['proportional'],
    license: {
      spdx: 'OFL-1.1', name: 'OFL', nameEn: 'OFL',
      confidence: 'auto-high',
    },
    converted: false,
    curated: true,
    glyphCount: 100,
    hanInk: null,
    inkHeight: 7,
    inkHeights: [7],
    badges: [],
    coverageSummary: {},
    coverage: [],
    variants: [{
      id: 'v', file: 'v.bdf', size: 12, weight: 'regular', spacing: 'proportional',
      width: 'normal', displaySize: 0, script: null, glyphs: 100,
    }],
    preview: '',
    sampleLang: 'latin',
    sampleText: '',
    previewVariant: '',
    added: '2026-08-01',
    searchText: '',
    ...over,
  };
}

const A = fam({
  searchText: '東雲 东云 Alpha 阿尔法 GalmuriExtended 俐方體11號 俐方体11号',
  slug: 'a', name: 'Alpha', names: { 'zh-Hans': '阿尔法' },
  authors: ['quiple', 'Lee Yerim'],
  sizes: [8, 16], inkHeight: 16, inkHeights: [11, 12, 13, 14, 16],
  vibes: ['cute'], glyphCount: 500, added: '2026-08-10',
});
const B = fam({
  slug: 'b', name: 'Beta', form: 'mingcho', scripts: ['zh-hans'],
  license: {
    spdx: 'GPL-2.0-only', name: 'GPL', nameEn: 'GPL',
    confidence: 'auto-high',
  },
  coverageSummary: { gb2312: 1 }, coverage: [], converted: true,
  spacing: ['monospaced'], weights: ['bold'], glyphCount: 7000, added: '2026-08-20',
});
const ALL = [A, B];

function run(over: Partial<FilterState>) {
  return applyFilters(ALL, { ...emptyState(), ...over }).map((f) => f.slug);
}

describe('applyFilters', () => {
  test('empty state keeps all, sorted by name', () => {
    expect(run({})).toEqual(['b', 'a']); // 阿尔法 vs Beta：localeCompare
  });

  test('q 简繁互通', () => {
    // searchText 由构建期做过简繁展开：家族名是「東雲」，搜「东云」也应命中
    expect(run({ q: '东云' })).toEqual(['a']);
    expect(run({ q: '東雲' })).toEqual(['a']);
  });

  test('q 命中名称、中文名与作者', () => {
    expect(run({ q: 'alpha' })).toEqual(['a']);
    expect(run({ q: '阿尔' })).toEqual(['a']);
    expect(run({ q: 'quiple' })).toEqual(['a']);
    // 并列作者的第二位也要能搜到
    expect(run({ q: 'Lee Yerim' })).toEqual(['a']);
    expect(run({ q: 'zzz' })).toEqual([]);
  });

  test('q 按空白拆词，全部命中才算', () => {
    // 「俐方」与「cubic」各自都在，合起来搜也该命中；
    // 整串当子串匹配的话，跨字段的组合永远落空
    expect(run({ q: '阿尔法 Alpha' })).toEqual(['a']);
    expect(run({ q: 'Alpha 阿尔法' })).toEqual(['a']);
    expect(run({ q: 'Alpha zzz' })).toEqual([]);
    expect(run({ q: '阿尔法　Alpha' })).toEqual(['a']); // 全角空格
  });

  test('q 命中 searchText 里的曾用名', () => {
    expect(run({ q: 'GalmuriExtended' })).toEqual(['a']);
    expect(run({ q: '俐方体11号' })).toEqual(['a']);
  });

  test('inkH 按任一变体命中', () => {
    // 文泉驿式：一个家族有 11/12/13/14/16 五档，按 14-14 也该命中；
    // 只比家族最大值的话就落空了
    expect(run({ inkH: [14, 14] })).toEqual(['a']);
    expect(run({ inkH: [12, 16] })).toEqual(['a']);
    expect(run({ inkH: [17, 20] })).toEqual([]);
  });

  test('forms', () => expect(run({ forms: ['mingcho'] })).toEqual(['b']));
  test('vibes', () => expect(run({ vibes: ['cute'] })).toEqual(['a']));
  test('sizes intersect', () => expect(run({ sizes: [16] })).toEqual(['a']));
  test('scripts', () => expect(run({ scripts: ['zh-hans'] })).toEqual(['b']));

  test('licenses incl unknown bucket', () => {
    expect(run({ licenses: ['GPL-2.0-only'] })).toEqual(['b']);
    const c = fam({
      slug: 'c',
      license: {
        spdx: null, name: '未识别', nameEn: 'Unknown',
        confidence: 'unknown',
      },
    });
    expect(
      applyFilters([c], { ...emptyState(), licenses: ['unknown'] }),
    ).toHaveLength(1);
  });

  test('spacing & weights', () => {
    expect(run({ spacing: ['monospaced'] })).toEqual(['b']);
    expect(run({ weights: ['bold'] })).toEqual(['b']);
  });

  test('coverage req', () =>
    expect(run({ coverage: [{ id: 'gb2312', min: 0.99 }] })).toEqual(['b']));

  test('chars via lookup', () => {
    const lookup = (slug: string) => slug === 'b';
    expect(
      applyFilters(ALL, { ...emptyState(), chars: '永' }, lookup).map((f) => f.slug),
    ).toEqual(['b']);
    // 无 lookup 时不筛（等待懒加载）
    expect(run({ chars: '永' })).toEqual(['b', 'a']);
  });

  test('sorts', () => {
    expect(run({ sort: 'size' })).toEqual(['a', 'b']);
    expect(run({ sort: 'glyphs' })).toEqual(['b', 'a']);
  });
});

describe('urlstate', () => {
  test('roundtrip identity', () => {
    const s: FilterState = {
      ...emptyState(),
      q: '像素',
      forms: ['gothic', 'mingcho'],
      vibes: ['cute'],
      sizes: [8, 16],
      inkH: [7, 15],
      scripts: ['ja'],
      licenses: ['OFL-1.1', 'unknown'],
      spacing: ['monospaced'],
      weights: ['bold'],
      coverage: [{ id: 'gb2312', min: 0.9 }],
      chars: '永',
      sort: 'glyphs',
    };
    expect(decodeState(encodeState(s))).toEqual(s);
  });

  test('unknown params ignored, bad values dropped', () => {
    const p = new URLSearchParams('foo=bar&sizes=8,abc&ink=x-y&sort=nope');
    const s = decodeState(p);
    expect(s.sizes).toEqual([8]);
    expect(s.inkH).toBeNull();
    expect(s.sort).toBe('name');
  });
});
