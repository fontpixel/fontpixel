import { expect, test } from 'vitest';
import { createRater, ratingOrder, sizeFactor } from './rating';
import { RATING_ADJUSTMENTS } from './rating-adjustments';
import { GOOGLE_FONTS_BONUS, GOOGLE_FONTS_FAMILIES } from './google-fonts';
import { existsSync, readFileSync, readdirSync } from 'node:fs';

const font = (coverageSummary: Record<string, number> = {}, sizes = [12], slug = 'font') =>
  ({ slug, sizes, coverageSummary, coverage: [] as number[] });
const rate = createRater();
const latin = { 'latin-basic': 1 };
const japanese = { ...latin, hiragana: 1, katakana: 1, 'jisx0208-l1': 1 };

test('Google Fonts receive one small family bonus and DotGothic16 has no aesthetic penalty', () => {
  for (const slug of GOOGLE_FONTS_FAMILIES) {
    const result = rate(font(latin, [12], slug));
    expect(result.googleFontsBonus).toBe(1);
    expect(result.score - result.automaticScore - result.adjustment).toBe(GOOGLE_FONTS_BONUS);
    const manyVariants = { ...font(latin, [12, 12, 16], slug), variants: Array(20).fill({ size: 12 }) };
    expect(rate(manyVariants).score)
      .toBe(result.score);
  }
  expect(rate(font(latin, [16], 'dotgothic16'))).toMatchObject({ adjustment: 0, score: 91 });
  expect(rate(font(latin, [12], 'ordinary')).googleFontsBonus).toBe(0);
});

test('reviewed Google Fonts list covers catalogue homepages and author-hosted families', () => {
  const root = new URL('../../../fonts/', import.meta.url);
  const expected = new Set(['tiny5', 'dotgothic16', 'jersey', 'jacquard']);
  for (const directory of readdirSync(root, { withFileTypes: true })) {
    if (!directory.isDirectory()) continue;
    const metadata = new URL(`${directory.name}/family.toml`, root);
    if (!existsSync(metadata)) continue;
    if (/^homepage\s*=\s*"https?:\/\/fonts\.google\.com(?:\/|\")/m.test(readFileSync(metadata, 'utf8'))) {
      expected.add(directory.name);
    }
  }
  expect([...GOOGLE_FONTS_FAMILIES].sort()).toEqual([...expected].sort());
});

test('aesthetic adjustments apply once after automatic scoring and retain headroom above 100', () => {
  const complete = { ...latin, 'latin1-supp': 1, 'latin-ext-a': 1, greek: 1,
    cp437: 1, 'box-drawing': 1, 'block-elements': 1 };
  const preferred = font(complete, [12], 'galmuri');
  const ordinary = font(complete, [12], 'ordinary');
  const smallerBonus = font(complete, [12], 'qiu-ye-yuan-ti-16');
  expect(rate(preferred)).toMatchObject({ automaticScore: 100, adjustment: 1.5, score: 101.5 });
  expect(rate(smallerBonus)).toMatchObject({ automaticScore: 100, adjustment: 0.5, score: 100.5 });
  expect(ratingOrder([ordinary, smallerBonus, preferred])).toEqual([preferred, smallerBonus, ordinary]);
  const licensed = rate({ ...preferred, license: { spdx: 'GPL-2.0-only' } });
  expect(licensed).toMatchObject({ automaticScore: 96, adjustment: 1.5, score: 97.5 });
  expect(rate(font({}, [12], 'misc-fixed')).score).toBe(0);
});

test('aesthetic preferences target exact existing families, including only regular Fusion Pixel', () => {
  for (const [slug, adjustment] of Object.entries(RATING_ADJUSTMENTS)) {
    expect(existsSync(new URL(`../../../fonts/${slug}/family.toml`, import.meta.url))).toBe(true);
    expect(rate(font(latin, [12], slug)).score).toBe(90 + adjustment);
  }
  expect(rate(font(latin, [12], 'fusion-pixel')).adjustment).toBe(1.5);
  for (const slug of ['zheng-ge-dian-hei-16', 'misc-fixed', 'dos-gothic', 'dos-saemmul',
    'jiskan', '1307', 'baekmuk-batang', 'baekmuk-dotum', 'baekmuk-gulim', 'baekmuk-hline',
    'fusion-bold-pixel', 'zlabs-diamondpix-16px', 'unknown', 'constructor']) {
    expect(rate(font(latin, [12], slug)).adjustment).toBe(0);
  }
});

test('size preferences are gentle, monotone outside 8–16 and neutral throughout that range', () => {
  for (let px = 8; px <= 16; px++) expect(sizeFactor([px])).toBe(1);
  for (let px = 1; px <= 7; px++) expect(sizeFactor([px])).toBeLessThan(sizeFactor([px + 1]));
  for (let px = 16; px <= 128; px++) expect(sizeFactor([px])).toBeGreaterThan(sizeFactor([px + 1]));
  expect(sizeFactor([7])).toBeGreaterThan(0.98);
  expect(sizeFactor([17])).toBeGreaterThan(0.98);
  expect(sizeFactor([1000])).toBeGreaterThan(0.88);
  expect(sizeFactor([5, 12, 64])).toBe(1);
  expect(sizeFactor([12, 12, 12])).toBe(1);
  expect(sizeFactor([0, NaN, -2])).toBe(1);
});

test('scores use coverage completeness, with a gentler curve for large CJK repertoires', () => {
  const partialLatin = rate(font({ 'latin-basic': 0.64 }));
  const partialChinese = rate(font({ ...latin, gb2312: 0.64 }));
  expect(partialChinese.target).toBe('zh-hans');
  expect(partialChinese.core).toBeCloseTo(0.8);
  expect(partialChinese.score).toBeGreaterThan(partialLatin.score);
  expect(partialChinese.score).toBeLessThan(rate(font({ ...latin, gb2312: 1 })).score);
  // Complete ASCII must not mask incomplete coverage of a CJK font's target.
  expect(partialChinese.score).toBeLessThan(rate(font(latin)).score);
});

test('Japanese is judged by its own target, rather than by overlapping Chinese subsets', () => {
  const result = rate(font({ ...japanese, gb2312: 0.5, 'big5-changyong': 0.8 }));
  expect(result.target).toBe('ja');
  expect(result.core).toBe(1);
  expect(result.score).toBeGreaterThanOrEqual(90);
  expect(rate(font({ ...latin, hiragana: 1, katakana: 1 })).target).toBe('ja');
  expect(rate(font({ ...japanese, hiragana: 0 })).target).toBe('latin');
});

test('Korean can complete the practical KS set without all 11,172 syllables or any hanja', () => {
  const result = rate(font({ ...latin, 'ksx1001-hangul': 1, 'hangul-syllables': 2350 / 11172 }));
  expect(result.target).toBe('ko');
  expect(result.core).toBe(1);
  expect(result.score).toBeGreaterThanOrEqual(90);
  expect(result.score).toBeLessThan(96);
});

test('alphabet targets work outside Latin, and incidental Greek does not become the main target', () => {
  for (const script of ['cyrillic', 'greek', 'arabic', 'thai']) {
    expect(rate(font({ [script]: 1 })).target).toBe(script);
    expect(rate(font({ [script]: 0.7 })).core).toBe(0.7);
  }
  expect(rate(font({ ...latin, greek: 0.2 })).target).toBe('latin');
  expect(rate(font({ ...latin, greek: 0.7 })).score).toBeGreaterThan(rate(font(latin)).score);
});

test('target depth dominates extras and adding more foreign scripts cannot keep stacking points', () => {
  expect(rate(font(latin)).score).toBe(90);
  const scores = [
    latin,
    { ...latin, 'latin1-supp': 1, 'latin-ext-a': 1 },
    { ...latin, 'latin1-supp': 1, 'latin-ext-a': 1, cyrillic: 1 },
    { ...latin, 'latin1-supp': 1, 'latin-ext-a': 1, cyrillic: 1, greek: 1 },
  ].map(coverage => rate(font(coverage)).score);
  expect(scores[1]).toBe(98);
  expect(scores[2]).toBe(99);
  expect(scores[3]).toBe(scores[2]);
  expect(rate(font({ ...latin, cp437: 1, 'box-drawing': 1, 'block-elements': 1 })).score).toBe(91);
  expect(rate(font({ ...latin, cp437: 1 })).score).toBe(90);
  expect(rate(font({ 'latin1-supp': 1, 'latin-ext-a': 1 })).score).toBe(0);
});

test('specialists can earn the same depth bonus without adding another language', () => {
  const profiles: Record<string, number>[] = [
    { ...latin, 'latin1-supp': 1, 'latin-ext-a': 1 },
    { gb2312: 1, 'tongyong-guifan': 1, 'gbk-hanzi': 1 },
    { 'big5-changyong': 1, big5: 1 },
    { ...japanese, 'jisx0208-l2': 1, 'jisx0213-l3': 1 },
    { 'ksx1001-hangul': 1, 'hangul-syllables': 1 },
  ];
  const scores = profiles.map(coverage => rate(font(coverage)).score);
  expect(new Set(scores).size).toBe(1);
  expect(scores[0]).toBe(98);
});

test('a complete Latin specialist can match a pan-CJK font without covering CJK', () => {
  const specialist = { ...latin, 'latin1-supp': 1, 'latin-ext-a': 1, greek: 1,
    cp437: 1, 'box-drawing': 1, 'block-elements': 1 };
  const broad = { ...specialist, ...japanese, gb2312: 1, 'gbk-hanzi': 1, 'tongyong-guifan': 1,
    'big5-changyong': 1, big5: 1, 'ksx1001-hangul': 1, 'hangul-syllables': 1,
    cyrillic: 1, arabic: 1, thai: 1 };
  expect(rate(font(specialist)).target).toBe('latin');
  expect(rate(font(specialist)).score).toBe(100);
  expect(rate(font(broad)).score).toBe(rate(font(specialist)).score);
});

test('overlapping Han references count as one extra dimension', () => {
  const base = { 'ksx1001-hangul': 1, 'hangul-syllables': 1, gb2312: 0.6 };
  const overlapping = { ...base, 'big5-changyong': 0.6, 'jisx0208-l1': 0.6, hiragana: 1, katakana: 1 };
  expect(rate(font(base)).target).toBe('ko');
  expect(rate(font(overlapping)).score).toBe(rate(font(base)).score);
});

test('WenQuanYi-like fonts with equal core coverage separate on useful additional support', () => {
  const song = font({ ...japanese, gb2312: 1, 'big5-changyong': 1, big5: 1,
    'gbk-hanzi': 1, 'tongyong-guifan': 0.9754,
    'latin1-supp': 0.6667, cyrillic: 0.6804, greek: 0.6667,
    cp437: 0.8196, 'box-drawing': 0.9141, 'block-elements': 0.625,
  }, [12, 13, 14, 15, 16], 'wqy-bitmap-song');
  const unibit = font({ ...song.coverageSummary,
    'latin1-supp': 1, 'latin-ext-a': 1, cyrillic: 1, greek: 1, arabic: 1, thai: 1,
    'ksx1001-hangul': 1, 'hangul-syllables': 1,
    cp437: 1, 'box-drawing': 1, 'block-elements': 1,
  }, [16], 'wqy-unibit');
  expect(rate(song).core).toBe(rate(unibit).core);
  expect(rate(song).size).toBe(rate(unibit).size);
  expect(rate(song).score).toBeLessThan(100);
  expect(rate(unibit).score).toBe(100);
  expect(ratingOrder([song, unibit])[0]).toBe(unibit);
});

test('more coverage cannot lower the result when switching between eligible CJK profiles', () => {
  let previous = 0;
  for (const coverage of [0.8, 0.9, 0.99, 1]) {
    const result = rate(font({ gb2312: coverage, 'big5-changyong': 0.9, big5: 1 }));
    expect(result.score).toBeGreaterThanOrEqual(previous);
    previous = result.score;
  }
});

test('family size, duplicate variants, glyph count and missing optional metadata do not inflate ratings', () => {
  const simple = font(latin);
  const inflated = { ...simple, glyphCount: 1000000, variants: Array(100).fill({ size: 12 }), sizes: [12, 12] };
  expect(rate(inflated)).toEqual(rate(simple));
  expect(rate(font()).score).toBe(0);
});

test('aligned full coverage ratios take precedence over summary fallback and malformed values are bounded', () => {
  const full = createRater(['latin-basic', 'latin1-supp', 'latin-ext-a']);
  const result = full({ ...font({ 'latin-basic': 0.2 }), coverage: [1, 1, 1] });
  expect(result.score).toBe(98);
  expect(full({ ...font(latin), coverage: [] }).score).toBe(90);
  expect(rate(font({ 'latin-basic': NaN })).score).toBe(0);
  expect(rate(font({ 'latin-basic': 2 })).score).toBe(90);
});

test('ranking is fixed, independent of input order, and filtering preserves relative order', () => {
  const fonts = [font(latin, [28], 'large'), font(latin, [12], 'z'), font(latin, [12], 'a'), font(latin, [5], 'tiny')];
  const ordered = ratingOrder(fonts);
  expect(ordered.map(f => f.slug)).toEqual(['a', 'z', 'tiny', 'large']);
  expect(ratingOrder([...fonts].reverse())).toEqual(ordered);
  expect(ratingOrder(fonts.filter(f => f.slug !== 'tiny'))).toEqual(ordered.filter(f => f.slug !== 'tiny'));
  expect(fonts[0]!.slug).toBe('large');
});
