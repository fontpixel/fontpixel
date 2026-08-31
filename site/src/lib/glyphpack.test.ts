import { readFileSync } from 'node:fs';
import { expect, test } from 'vitest';
import { GlyphChunk } from './glyphpack';

function fixture(): ArrayBuffer {
  const buf = readFileSync(new URL('./__fixtures__/mini-chunk.bin', import.meta.url));
  return buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength) as ArrayBuffer;
}

test('parses python-written chunk', () => {
  const c = GlyphChunk.parse(fixture());
  expect(c.size).toBe(2);
  expect(c.rangeStart).toBe(0);
  expect(c.rangeEnd).toBe(0x110000);
  const a = c.get(65)!;
  expect([a.dwidth, a.w, a.h, a.xoff, a.yoff]).toEqual([8, 7, 10, 0, 0]);
  expect(a.rows.length).toBe(10); // ceil(7/8)=1 byte/row x 10 rows
  expect(a.rows[0]).toBe(0x30);
  expect(a.rows[5]).toBe(0xfc);
  const yong = c.get(27704)!;
  expect([yong.dwidth, yong.w, yong.h, yong.xoff, yong.yoff]).toEqual([16, 16, 15, 0, -1]);
  expect(yong.rows.length).toBe(30);
});

test('missing codepoints return null', () => {
  const c = GlyphChunk.parse(fixture());
  expect(c.get(66)).toBeNull();
  expect(c.has(27704)).toBe(true);
  expect(c.has(0x4e00)).toBe(false);
});

test('rejects bad magic', () => {
  const bad = new Uint8Array(fixture().slice(0));
  bad[0] = 0x58;
  expect(() => GlyphChunk.parse(bad.buffer as ArrayBuffer)).toThrow();
});
