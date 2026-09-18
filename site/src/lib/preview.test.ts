import { expect, test } from 'vitest';
import { FamilyIndexSchema } from './schema';
import fixture from './__fixtures__/index.fixture.json';
import { previewFor } from './preview';

const family = FamilyIndexSchema.parse(fixture.families[0]);
const specimen = (variantId: string) => ({ variantId, text: variantId, file: `${variantId}.svg` });
const multilingual = {
  ...family,
  sampleLang: 'zh-Hans',
  previews: {
    'zh-Hans': specimen('simplified'),
    'zh-Hant': specimen('traditional'),
    ja: specimen('japanese'),
    ko: specimen('korean'),
    latin: specimen('latin'),
  },
};

test.each([
  ['zh-Hans', 'simplified'], ['zh-Hant', 'traditional'], ['ja', 'japanese'],
  ['ko', 'korean'], ['latin', 'latin'],
])('a %s default sample uses matching glyph forms', (sampleLang, id) => {
  expect(previewFor({ ...multilingual, sampleLang })).toEqual({
    sampleLang, ...specimen(id),
  });
});

test('an unavailable sample preview keeps the family specimen', () => {
  expect(previewFor({ ...multilingual, sampleLang: 'thai' })).toEqual({
    sampleLang: 'thai',
    variantId: family.previewVariant, text: family.sampleText, file: family.preview,
  });
});

test('old data keeps the family specimen', () => {
  expect(previewFor(family)).toMatchObject({
    variantId: family.previewVariant, text: family.sampleText, file: family.preview,
  });
});

test.each([
  [[[10, 1661], [13, 3298], [20, 5263]], '13'],
  [[[7, 1000], [8, 100]], '8'],
  [[[16, 100], [17, 1000]], '16'],
  [[[7, 100], [20, 1000]], '20'],
  [[[8, 200], [16, 100]], '8'],
])('fallback preview prefers 8–16px before glyph count: %j', (sizes, expected) => {
  const variants = sizes.map(([size, glyphs]) => ({ ...family.variants[0]!, id: String(size), size, glyphs }));
  expect(previewFor({ ...family, previews: undefined, previewVariant: '', variants }).variantId).toBe(expected);
});
