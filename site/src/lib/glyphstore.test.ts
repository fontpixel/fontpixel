import { readFileSync } from 'node:fs';
import { expect, test, vi } from 'vitest';
import { GlyphStore } from './glyphstore';

const PACK_DIR = new URL('./__fixtures__/pack-mini/', import.meta.url);

function makeFetch() {
  const calls: string[] = [];
  const fetchFn = vi.fn(async (url: string) => {
    calls.push(url);
    const name = url.split('/').pop()!;
    const buf = readFileSync(new URL(name, PACK_DIR));
    const body = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
    return {
      ok: true,
      status: 200,
      arrayBuffer: async () => body,
      json: async () => JSON.parse(buf.toString('utf-8')),
    } as unknown as Response;
  });
  return { fetchFn, calls };
}

test('core pack satisfies ascii without extra chunk fetch', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/data', fetchFn as unknown as typeof fetch);
  const map = await store.glyphsFor('mini', 'mini', 'A');
  expect(map.get(65)?.w).toBe(7);
  expect(calls.filter((c) => c.endsWith('manifest.json'))).toHaveLength(1);
  expect(calls.filter((c) => c.endsWith('core.bin.gz'))).toHaveLength(1);
  expect(calls.some((c) => c.includes('00006c00'))).toBe(false);
});

test('non-core char triggers range chunk fetch, cached afterwards', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/data', fetchFn as unknown as typeof fetch);
  const map = await store.glyphsFor('mini', 'mini', '永');
  expect(map.get(27704)?.w).toBe(16);
  expect(calls.filter((c) => c.includes('00006c00-00006d00'))).toHaveLength(1);
  await store.glyphsFor('mini', 'mini', '永永永');
  expect(calls.filter((c) => c.includes('00006c00-00006d00'))).toHaveLength(1);
});

test('concurrent requests dedupe inflight fetches', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/data', fetchFn as unknown as typeof fetch);
  await Promise.all([
    store.glyphsFor('mini', 'mini', '永'),
    store.glyphsFor('mini', 'mini', '永A'),
  ]);
  expect(calls.filter((c) => c.includes('00006c00-00006d00'))).toHaveLength(1);
  expect(calls.filter((c) => c.endsWith('manifest.json'))).toHaveLength(1);
});

test('chars outside any range resolve to null', async () => {
  const { fetchFn } = makeFetch();
  const store = new GlyphStore('/data', fetchFn as unknown as typeof fetch);
  const map = await store.glyphsFor('mini', 'mini', '龘');
  expect(map.get(0x9f98)).toBeNull();
});

test('lru evicts old chunks', async () => {
  const { fetchFn, calls } = makeFetch();
  const store = new GlyphStore('/data', fetchFn as unknown as typeof fetch, 1);
  await store.glyphsFor('mini', 'mini', '永'); // chunk 6c00 进入容量 1 的缓存
  await store.glyphsFor('mini', 'mini', 'A'); // core 不占 LRU；再取 65 无新 chunk
  await store.glyphsFor('mini', 'mini', '天'); // 0x5929 无区块 → 无 fetch
  await store.glyphsFor('mini', 'mini', '永');
  const chunkCalls = calls.filter((c) => c.includes('00006c00-00006d00'));
  expect(chunkCalls.length).toBe(1); // 容量 1 且未被其他 chunk 挤出 → 仍缓存
});
