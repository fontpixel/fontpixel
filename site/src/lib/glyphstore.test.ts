import { readFileSync } from 'node:fs';
import { gzipSync } from 'node:zlib';
import { expect, test, vi } from 'vitest';
import { GlyphStore } from './glyphstore';
import { decodeBdf } from './bdf';
const source = readFileSync(new URL('../../../pipeline/tests/fixtures/mini.bdf', import.meta.url));
const compressed = gzipSync(source);
function makeFetch() {
  const calls: string[] = [];
  const fetchFn = vi.fn(async (url: string) => { calls.push(url); return new Response(compressed); });
  return { fetchFn: fetchFn as unknown as typeof fetch, calls };
}
test('one BDF download serves default and arbitrary text', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/data', fetchFn);
  const map = await store.glyphsFor('mini', 'mini', 'A永龘');
  expect(map.get(65)).toMatchObject({ w: 7, h: 10, dwidth: 8 });
  expect([...map.get(65)!.rows]).toEqual([0x30, 0x30, 0x48, 0x48, 0x84, 0xfc, 0x84, 0x84, 0x84, 0x84]);
  expect(map.get(27704)).toMatchObject({ w: 16, h: 15, yoff: -1 });
  expect(map.get(0x9f98)).toBeNull();
  await store.glyphsFor('mini', 'mini', '永永永');
  expect(calls).toEqual(['/downloads/mini--mini.bdf.gz']);
  const font = await store.loadFont('mini', 'mini');
  expect(font.glyphCount).toBe(2);
  expect(font.ranges.map((r) => r.start)).toEqual([0, 0x6c00]);
});
test('concurrent requests share a download', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/base/data', fetchFn);
  await Promise.all([store.loadFont('mini', 'mini'), store.glyphsFor('mini', 'mini', '永A')]);
  expect(calls).toEqual(['/base/downloads/mini--mini.bdf.gz']);
});
test('whole-font cache evicts old variants', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/data', fetchFn, 1);
  await store.loadFont('mini', 'a');
  await store.loadFont('mini', 'b');
  await store.loadFont('mini', 'a');
  expect(calls).toHaveLength(3);
});
test('failed downloads can be retried', async () => {
  let attempt = 0;
  const fetchFn = vi.fn(async () => ++attempt === 1 ? new Response('', { status: 503 }) : new Response(compressed));
  const store = new GlyphStore('/data', fetchFn);
  await expect(store.glyphsFor('mini', 'mini', 'A')).rejects.toThrow('503');
  expect((await store.glyphsFor('mini', 'mini', 'A')).get(65)).not.toBeNull();
});
test('accepts BDF already decompressed by HTTP', async () => {
  const font = await decodeBdf(Uint8Array.from(source).buffer);
  expect(font.pixelSize).toBe(16);
  expect(font.ascent).toBe(14);
  expect(font.descent).toBe(2);
  expect(font.glyphs.has(-1)).toBe(false);
});
test('retains supplementary Unicode codepoints and glyph metrics', async () => {
  const bdf = source.toString().replace('ENCODING 27704', 'ENCODING 131072');
  const fetchFn = vi.fn(async () => new Response(gzipSync(bdf)));
  const store = new GlyphStore('/data', fetchFn);
  const map = await store.glyphsFor('mini', 'mini', '𠀀');
  expect([...map.keys()]).toEqual([0x20000]);
  expect(map.get(0x20000)).toMatchObject({ w: 16, h: 15, yoff: -1, dwidth: 16 });
});
