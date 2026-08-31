import { readFileSync } from 'node:fs';
import { expect, test } from 'vitest';
import { GlyphChunk, type DecodedGlyph } from './glyphpack';
import { rasterize, MISSING_ADVANCE } from './render';

const FONT = { pixelSize: 16, ascent: 14, descent: 2 };

function glyphs(): Map<number, DecodedGlyph | null> {
  const buf = readFileSync(new URL('./__fixtures__/mini-chunk.bin', import.meta.url));
  const c = GlyphChunk.parse(
    buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as ArrayBuffer,
  );
  const m = new Map<number, DecodedGlyph | null>();
  m.set(65, c.get(65));
  m.set(27704, c.get(27704));
  return m;
}

function px(r: { width: number; data: Uint8ClampedArray }, x: number, y: number): number[] {
  const i = (y * r.width + x) * 4;
  return [r.data[i]!, r.data[i + 1]!, r.data[i + 2]!, r.data[i + 3]!];
}

test('renders single glyph at correct pixels', () => {
  const r = rasterize('A', glyphs(), FONT, { invert: false });
  expect(r.width).toBe(8); // dwidth
  expect(r.height).toBe(16); // ascent+descent
  // A row 0 is 0x30 -> x=2,3; py = ascent - (yoff+h) = 14-10 = 4
  expect(px(r, 2, 4)[3]).toBe(255);
  expect(px(r, 2, 4)[0]).toBeLessThan(64); // ink color
  expect(px(r, 0, 0)[0]).toBeGreaterThan(200); // paper color
  expect(r.missing).toEqual([]);
});

test('missing char produces box and missing list', () => {
  const r = rasterize('B', glyphs(), FONT, { invert: false });
  expect(r.missing).toEqual([66]);
  expect(r.width).toBe(MISSING_ADVANCE(16));
  // some edge pixel of the dashed box should be ink-colored
  expect(px(r, 0, 14 - 1)[3]).toBe(255);
});

test('newline breaks lines', () => {
  const r = rasterize('A\nA', glyphs(), FONT, { invert: false });
  expect(r.height).toBe(16 * 2 + 1); // lineGap = 1
  expect(r.width).toBe(8);
});

test('invert swaps ink and paper', () => {
  const norm = rasterize('A', glyphs(), FONT, { invert: false });
  const inv = rasterize('A', glyphs(), FONT, { invert: true });
  expect(px(norm, 0, 0)[0]).toBeGreaterThan(200);
  expect(px(inv, 0, 0)[0]).toBeLessThan(64);
  expect(px(inv, 2, 4)[0]).toBeGreaterThan(200);
});

test('maxWidth wraps at char boundary', () => {
  const r = rasterize('AA', glyphs(), FONT, {
    invert: false, maxWidth: 10,
  });
  expect(r.height).toBe(33);
  expect(r.width).toBe(8);
});

test('cjk glyph with negative yoff extends below baseline', () => {
  const r = rasterize('永', glyphs(), FONT, { invert: false });
  expect(r.width).toBe(16);
  // 永 bby=-1, bottom row py = 14 - (-1) - 1 = 14
  let anyInkRow14 = false;
  for (let x = 0; x < 16; x++) if (px(r, x, 14)[3] === 255 && px(r, x, 14)[0] < 64) anyInkRow14 = true;
  expect(anyInkRow14).toBe(true);
});

test('字形高过 FONT_ASCENT 时不削顶（萤火飞回归）', () => {
  // place a glyph reaching height 6 in a font with ascent=4: effective row height should expand to 6+descent
  const tall = {
    cp: 0x65e5,
    w: 3,
    h: 6,
    xoff: 0,
    yoff: 0,
    dwidth: 4,
    rows: new Uint8Array([0xe0, 0xa0, 0xa0, 0xa0, 0xa0, 0xe0]),
  };
  const map = new Map([[0x65e5, tall]]);
  const r = rasterize('日', map, { pixelSize: 6, ascent: 4, descent: 1 }, { invert: false });
  expect(r.height).toBe(7); // 6 + 1, not the declared 4 + 1
  // top row pixels must exist (not clipped)
  const topRow = Array.from({ length: r.width }, (_, x) => r.mask[x]);
  expect(topRow.some((v) => v === 1)).toBe(true);
});
