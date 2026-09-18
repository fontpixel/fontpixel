import { describe, expect, test } from 'vitest';
import { applyFilters, emptyState, type FilterState } from './filters';
import { decodeState, encodeState } from './urlstate';
import type { FamilyIndex } from './schema';

function fam(over: Partial<FamilyIndex>): FamilyIndex {
  return {
    slug: 'x',
    cardPreview: '',
    namePreviews: {},
    name: 'X',
    names: { en: 'X' },
    authors: [],
    authorsEn: [],
    forms: ['gothic', 'sans'],
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
  coverageSummary: { 'latin-basic': 1, 'latin1-supp': 1, 'latin-ext-a': 1 },
});
const B = fam({
  slug: 'b', name: 'Beta', forms: ['song', 'serif'], scripts: ['zh-hans'],
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
  test('empty state sorts by fixed rating, regardless of input order', () => {
    expect(run({})).toEqual(['a', 'b']);
    expect(applyFilters([B, A], emptyState()).map(f => f.slug)).toEqual(['a', 'b']);
  });

  test('q 简繁互通', () => {
    // searchText gets Simplified/Traditional expansion at build time: family name is "東雲", searching "东云" should also match
    expect(run({ q: '东云' })).toEqual(['a']);
    expect(run({ q: '東雲' })).toEqual(['a']);
  });

  test('q 命中名称、中文名与作者', () => {
    expect(run({ q: 'alpha' })).toEqual(['a']);
    expect(run({ q: '阿尔' })).toEqual(['a']);
    expect(run({ q: 'quiple' })).toEqual(['a']);
    // the second co-author should also be searchable
    expect(run({ q: 'Lee Yerim' })).toEqual(['a']);
    expect(run({ q: 'zzz' })).toEqual([]);
  });

  test('q 按空白拆词，全部命中才算', () => {
    // "俐方" and "cubic" are each present, so a combined search should also match;
    // if matched as a whole substring, a cross-field combination would never match
    expect(run({ q: '阿尔法 Alpha' })).toEqual(['a']);
    expect(run({ q: 'Alpha 阿尔法' })).toEqual(['a']);
    expect(run({ q: 'Alpha zzz' })).toEqual([]);
    expect(run({ q: '阿尔法　Alpha' })).toEqual(['a']); // full-width space
  });

  test('q 命中 searchText 里的曾用名', () => {
    expect(run({ q: 'GalmuriExtended' })).toEqual(['a']);
    expect(run({ q: '俐方体11号' })).toEqual(['a']);
  });

  test('inkH 按任一变体命中', () => {
    // wenquanyi-style: a family has five tiers 11/12/13/14/16, searching 14-14 should also match;
    // comparing only against the family's max would miss it
    expect(run({ inkH: [14, 14] })).toEqual(['a']);
    expect(run({ inkH: [12, 16] })).toEqual(['a']);
    expect(run({ inkH: [17, 20] })).toEqual([]);
  });

  test('categories match any selected category without duplicating fonts', () => {
    expect(run({ forms: ['song'] })).toEqual(['b']);
    expect(run({ forms: ['serif'] })).toEqual(['b']);
    expect(run({ forms: ['sans'] })).toEqual(['a']);
    expect(run({ forms: ['gothic', 'sans'] })).toEqual(['a']);
    expect(run({ forms: ['sans', 'song'] })).toEqual(['a', 'b']);
    expect(run({ forms: ['rounded'] })).toEqual([]);
  });
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
    // without a lookup, don't filter (waiting on lazy load)
    expect(run({ chars: '永' })).toEqual(['a', 'b']);
  });

  test('sorts', () => {
    expect(run({ sort: 'name' })).toEqual(['b', 'a']);
    expect(run({ sort: 'size' })).toEqual(['a', 'b']);
    expect(run({ sort: 'glyphs' })).toEqual(['b', 'a']);
  });

  test('each reverse order mirrors the entire forward order, including ties', () => {
    const fonts = [...ALL, { ...A, slug: 'c' }];
    for (const sort of ['rating', 'name', 'size', 'glyphs'] as const) {
      const forward = applyFilters(fonts, { ...emptyState(), sort }).map(f => f.slug);
      const reverse = applyFilters(fonts, { ...emptyState(), sort: `${sort}-reverse` }).map(f => f.slug);
      expect(reverse).toEqual(forward.toReversed());
    }
  });
});

describe('urlstate', () => {
  test('legacy category links normalize and deduplicate their values', () => {
    const state = decodeState(new URLSearchParams('forms=mingcho,song,round,rounded,serif-pixel'));
    expect(state.forms).toEqual(['song', 'rounded', 'serif']);
    expect(encodeState(state).get('forms')).toBe('song,rounded,serif');
  });

  test('roundtrip identity', () => {
    const s: FilterState = {
      ...emptyState(),
      q: '像素',
      forms: ['gothic', 'song'],
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
    expect(s.sort).toBe('rating');
  });
  test('every reverse sort survives URL serialization', () => {
    for (const sort of ['rating-reverse', 'name-reverse', 'size-reverse', 'glyphs-reverse'] as const) {
      const state = { ...emptyState(), sort };
      expect(encodeState(state).get('sort')).toBe(sort);
      expect(decodeState(encodeState(state))).toEqual(state);
    }
  });
  test('default rating needs no URL parameter and replaces old random links', () => {
    expect(encodeState(emptyState()).toString()).toBe('');
    expect(decodeState(new URLSearchParams('sort=rating')).sort).toBe('rating');
    expect(decodeState(new URLSearchParams('sort=random')).sort).toBe('rating');
    expect(encodeState({ ...emptyState(), sort: 'name' }).get('sort')).toBe('name');
  });
});
