import { expect, test } from 'vitest';
import { toBdfText, toDotText } from './dotcopy';
import type { DecodedGlyph } from './glyphpack';

function raster(rows: string[]) {
  const width = rows[0]!.length;
  const height = rows.length;
  const mask = new Uint8Array(width * height);
  rows.forEach((r, y) =>
    [...r].forEach((c, x) => {
      if (c === '#') mask[y * width + x] = 1;
    }),
  );
  return { width, height, data: new Uint8ClampedArray(), missing: [], mask };
}

test('dot text mirrors the ink mask and trims blank top and bottom', () => {
  const r = raster(['....', '.##.', '#..#', '....']);
  expect(toDotText(r)).toBe('.##.\n#..#');
});

test('dot text of an empty raster is empty, not a block of dots', () => {
  expect(toDotText(raster(['...', '...']))).toBe('');
});

const A: DecodedGlyph = {
  cp: 0x41,
  dwidth: 6,
  w: 5,
  h: 2,
  xoff: 0,
  yoff: -1,
  // 每行按字节对齐、高位在左：0b10101000 = 0xA8
  rows: new Uint8Array([0xa8, 0x50]),
};

test('bdf export writes a pastable STARTCHAR block', () => {
  const out = toBdfText('A', new Map([[0x41, A]]));
  expect(out.split('\n')).toEqual([
    'STARTCHAR U+0041',
    'ENCODING 65',
    'SWIDTH 0 0',
    'DWIDTH 6 0',
    'BBX 5 2 0 -1',
    'BITMAP',
    'A8',
    '50',
    'ENDCHAR',
  ]);
});

test('bdf export emits each character once and skips missing ones', () => {
  const out = toBdfText('AA\nB', new Map([[0x41, A]]));
  expect(out.match(/STARTCHAR/g)).toHaveLength(1); // A 只出现一次，B 缺字跳过
});
