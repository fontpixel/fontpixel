import { readFileSync } from 'node:fs';
import { expect, test } from 'vitest';
import { CoverageIndex } from './intervals';

function fixture(): ArrayBuffer {
  const buf = readFileSync(
    new URL('./__fixtures__/coverage-intervals.bin', import.meta.url),
  );
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as ArrayBuffer;
}

test('parses python-written intervals', () => {
  const idx = CoverageIndex.parse(fixture());
  expect(idx.has('mini', 65)).toBe(true);
  expect(idx.has('mini', 27704)).toBe(true);
  expect(idx.has('mini', 66)).toBe(false);
  expect(idx.has('nometa', 65)).toBe(true);
  expect(idx.has('ghost', 65)).toBe(false);
});

test('covers checks every non-space char', () => {
  const idx = CoverageIndex.parse(fixture());
  expect(idx.covers('mini', '永')).toBe(true);
  expect(idx.covers('mini', 'A 永')).toBe(true); // whitespace skipped
  expect(idx.covers('mini', '龘')).toBe(false);
  expect(idx.covers('mini', 'A龘')).toBe(false);
});

test('covers can be asked of one variant, and shared sets are resolved per variant', () => {
  const idx = CoverageIndex.parse(fixture());
  expect(idx.covers('mini', 'A永', 'mini')).toBe(true);
  expect(idx.covers('mini', 'A永', 'mini2')).toBe(false);
  expect(idx.covers('mini', 'A', 'mini-bold')).toBe(true);
  expect(idx.covers('mini', 'A', 'ghost')).toBe(false);
  // Without a variant, one variant must have every character: A and 永 split
  // across two variants would not count.
  expect(idx.covers('mini', 'A永')).toBe(true);
  expect(idx.covers('nometa', '永', 'pixfont')).toBe(true);
});
