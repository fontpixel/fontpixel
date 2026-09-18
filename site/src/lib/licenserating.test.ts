import { expect, test } from 'vitest';
import { licenseFactor } from './licenserating';
import { createRater, ratingOrder } from './rating';

test('license preferences distinguish font exceptions and keep OFL at the normal baseline', () => {
  for (const id of ['MIT', 'BSD-2-Clause', 'CC0-1.0', 'OFL-1.1', 'Unlicense', 'LicenseRef-Mplus']) {
    expect(licenseFactor(id)).toBe(1);
  }
  for (const version of ['2.0', '3.0']) {
    const plain = licenseFactor(`GPL-${version}-only`);
    const exception = licenseFactor(`GPL-${version}-with-font-exception`);
    expect(plain).toBe(0.96);
    expect(exception).toBe(0.985);
    expect(licenseFactor(`GPL-${version}-or-later WITH Font-exception-2.0`)).toBe(exception);
    expect(licenseFactor(`GPL-${version}-only WITH Classpath-exception-2.0`)).toBe(plain);
  }
  expect(licenseFactor('CC-BY-SA-4.0')).toBe(0.98);
});

test('alternative licenses take the easier choice, combined licenses retain both obligations', () => {
  expect(licenseFactor('OFL-1.1 OR GPL-2.0-with-font-exception')).toBe(1);
  expect(licenseFactor('LicenseRef-PublicDomain AND OFL-1.1')).toBe(1);
  expect(licenseFactor('MIT AND GPL-2.0-only')).toBe(0.96);
  expect(licenseFactor('GPL-2.0-only OR MIT AND GPL-3.0-with-font-exception')).toBe(0.985);
  expect(licenseFactor('(GPL-2.0-only OR MIT) AND GPL-3.0-with-font-exception')).toBe(0.985);
  expect(licenseFactor('MIT OR (GPL-2.0-only AND GPL-3.0-only)')).toBe(1);
});

test('unknown or malformed metadata stays neutral rather than implying a restriction', () => {
  for (const id of [null, undefined, '', 'LicenseRef-Unreviewed', 'MIT OR', '(MIT', 'GPL-2.0-only WITH']) {
    expect(licenseFactor(id)).toBe(1);
  }
});

test('the shared rater applies the small license preference without rescuing missing coverage', () => {
  const base = { slug: 'font', sizes: [12], coverage: [], coverageSummary: { 'latin-basic': 1 } };
  const font = (spdx: string) => ({ ...base, slug: spdx, license: { spdx } });
  const rate = createRater();
  const mit = font('MIT'), exception = font('GPL-2.0-with-font-exception'), gpl = font('GPL-2.0-only');
  expect(rate(mit).score).toBe(90);
  expect(rate(exception).score).toBeCloseTo(88.65);
  expect(rate(gpl).score).toBeCloseTo(86.4);
  expect(ratingOrder([gpl, mit, exception])).toEqual([mit, exception, gpl]);
  expect(rate({ ...mit, coverageSummary: {} }).score).toBe(0);
});
