import { describe, expect, test } from 'vitest';
import { applyFilters, emptyState, type FilterState } from './filters';
import { decodeState, encodeState } from './urlstate';
import type { FamilyIndex } from './schema';

function fam(over: Partial<FamilyIndex>): FamilyIndex {
  return {
    slug: 'x',
    name: 'X',
    nameZh: '',
    author: '',
    form: 'gothic',
    vibes: [],
    scripts: ['latin'],
    sizes: [12],
    weights: ['regular'],
    spacing: ['proportional'],
    license: { spdx: 'OFL-1.1', name: 'OFL', commercial: true, confidence: 'auto-high' },
    converted: false,
    curated: true,
    glyphCount: 100,
    hanInk: null,
    inkHeight: 11,
    badges: [],
    coverageSummary: { gb2312: 0.5 },
    variants: [
      { id: 'v', file: 'v.bdf', size: 12, weight: 'regular', spacing: 'proportional', script: null, glyphs: 100 },
    ],
    preview: '',
    sampleLang: 'latin',
    added: '2026-08-01',
    ...over,
  };
}

const A = fam({ slug: 'a', name: 'Alpha', nameZh: '阿尔法', author: 'quiple', sizes: [8, 16], inkHeight: 7, vibes: ['cute'], glyphCount: 500, added: '2026-08-10' });
const B = fam({ slug: 'b', name: 'Beta', form: 'mingcho', scripts: ['zh-hans'], license: { spdx: 'GPL-2.0-only', name: 'GPL', commercial: null, confidence: 'auto-high' }, coverageSummary: { gb2312: 1 }, converted: true, spacing: ['monospaced'], weights: ['bold'], glyphCount: 7000, added: '2026-08-20' });
const ALL = [A, B];

function run(over: Partial<FilterState>) {
  return applyFilters(ALL, { ...emptyState(), ...over }).map((f) => f.slug);
}

describe('applyFilters', () => {
  test('empty state keeps all, sorted by name', () => {
    expect(run({})).toEqual(['b', 'a']); // 阿尔法 vs Beta:localeCompare
  });
  test('q matches name/nameZh/author', () => {
    expect(run({ q: 'alpha' })).toEqual(['a']);
    expect(run({ q: '阿尔' })).toEqual(['a']);
    expect(run({ q: 'quiple' })).toEqual(['a']);
    expect(run({ q: 'zzz' })).toEqual([]);
  });
  test('forms', () => expect(run({ forms: ['mingcho'] })).toEqual(['b']));
  test('vibes', () => expect(run({ vibes: ['cute'] })).toEqual(['a']));
  test('sizes intersect', () => expect(run({ sizes: [16] })).toEqual(['a']));
  test('inkH range', () => expect(run({ inkH: [10, 12] })).toEqual(['b']));
  test('scripts', () => expect(run({ scripts: ['zh-hans'] })).toEqual(['b']));
  test('licenses incl unknown bucket', () => {
    expect(run({ licenses: ['GPL-2.0-only'] })).toEqual(['b']);
    const c = fam({ slug: 'c', license: { spdx: null, name: '未识别', commercial: null, confidence: 'unknown' } });
    expect(applyFilters([c], { ...emptyState(), licenses: ['unknown'] })).toHaveLength(1);
  });
  test('commercialOnly', () => expect(run({ commercialOnly: true })).toEqual(['a']));
  test('spacing & weights', () => {
    expect(run({ spacing: ['monospaced'] })).toEqual(['b']);
    expect(run({ weights: ['bold'] })).toEqual(['b']);
  });
  test('origin', () => {
    expect(run({ origin: 'native' })).toEqual(['a']);
    expect(run({ origin: 'converted' })).toEqual(['b']);
  });
  test('coverage req', () => expect(run({ coverage: [{ id: 'gb2312', min: 0.99 }] })).toEqual(['b']));
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
    expect(run({ sort: 'added' })).toEqual(['b', 'a']);
  });
});

describe('urlstate', () => {
  test('roundtrip identity', () => {
    const s: FilterState = {
      q: '像素',
      forms: ['gothic', 'mingcho'],
      vibes: ['cute'],
      sizes: [8, 16],
      inkH: [7, 15],
      scripts: ['ja'],
      licenses: ['OFL-1.1', 'unknown'],
      commercialOnly: true,
      spacing: ['monospaced'],
      weights: ['bold'],
      origin: 'native',
      coverage: [{ id: 'gb2312', min: 0.99 }, { id: 'hiragana', min: 1 }],
      chars: '龘齉',
      sort: 'glyphs',
    };
    expect(decodeState(encodeState(s))).toEqual(s);
  });
  test('empty state encodes to empty query', () => {
    expect(encodeState(emptyState()).toString()).toBe('');
  });
  test('unknown params ignored, bad values dropped', () => {
    const p = new URLSearchParams('foo=bar&sizes=8,abc&ink=x-y&sort=nope&or=weird');
    const s = decodeState(p);
    expect(s.sizes).toEqual([8]);
    expect(s.inkH).toBeNull();
    expect(s.sort).toBe('name');
    expect(s.origin).toBe('all');
  });
});
