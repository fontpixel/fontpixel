/** 字形数据存取:manifest 缓存 + 分块 LRU + 并发去重(契约 C4)。 */

import { gunzip } from './decompress';
import { GlyphChunk, type DecodedGlyph } from './glyphpack';

export interface VariantManifest {
  version: 1;
  slug: string;
  variantId: string;
  pixelSize: number;
  ascent: number;
  descent: number;
  glyphCount: number;
  core: { file: string; gzBytes: number; glyphs: number };
  ranges: { start: number; end: number; file: string; gzBytes: number; glyphs: number }[];
}

export class GlyphStore {
  private manifests = new Map<string, Promise<VariantManifest>>();
  private cores = new Map<string, Promise<GlyphChunk>>();
  private chunks = new Map<string, Promise<GlyphChunk>>(); // 插入序即 LRU 序

  private readonly fetchFn: typeof fetch;

  constructor(
    private readonly dataBase: string,
    fetchFn?: typeof fetch,
    private readonly capacity = 64,
  ) {
    // 不能直接存全局 fetch:经 this 调用会 Illegal invocation
    this.fetchFn = fetchFn ?? ((input, init) => globalThis.fetch(input, init));
  }

  private url(slug: string, variantId: string, file: string): string {
    return `${this.dataBase}/packs/${slug}/${variantId}/${file}`;
  }

  private async fetchChunk(url: string): Promise<GlyphChunk> {
    const res = await this.fetchFn(url);
    if (!res.ok) throw new Error(`fetch ${url}: ${res.status}`);
    return GlyphChunk.parse(await gunzip(await res.arrayBuffer()));
  }

  loadManifest(slug: string, variantId: string): Promise<VariantManifest> {
    const key = `${slug}/${variantId}`;
    let p = this.manifests.get(key);
    if (!p) {
      p = this.fetchFn(this.url(slug, variantId, 'manifest.json')).then((r) => {
        if (!r.ok) throw new Error(`manifest ${key}: ${r.status}`);
        return r.json() as Promise<VariantManifest>;
      });
      p.catch(() => this.manifests.delete(key));
      this.manifests.set(key, p);
    }
    return p;
  }

  private coreChunk(slug: string, variantId: string, m: VariantManifest): Promise<GlyphChunk> {
    const key = `${slug}/${variantId}`;
    let p = this.cores.get(key);
    if (!p) {
      p = this.fetchChunk(this.url(slug, variantId, m.core.file));
      p.catch(() => this.cores.delete(key));
      this.cores.set(key, p);
    }
    return p;
  }

  private rangeChunk(
    slug: string,
    variantId: string,
    file: string,
  ): Promise<GlyphChunk> {
    const key = `${slug}/${variantId}/${file}`;
    let p = this.chunks.get(key);
    if (p) {
      // LRU 刷新
      this.chunks.delete(key);
      this.chunks.set(key, p);
      return p;
    }
    p = this.fetchChunk(this.url(slug, variantId, file));
    p.catch(() => this.chunks.delete(key));
    this.chunks.set(key, p);
    while (this.chunks.size > this.capacity) {
      const oldest = this.chunks.keys().next().value as string;
      this.chunks.delete(oldest);
    }
    return p;
  }

  async glyphsFor(
    slug: string,
    variantId: string,
    text: string,
  ): Promise<Map<number, DecodedGlyph | null>> {
    const cps = new Set<number>();
    for (const ch of text) {
      const cp = ch.codePointAt(0)!;
      if (cp !== 0x0a) cps.add(cp);
    }
    const out = new Map<number, DecodedGlyph | null>();
    if (cps.size === 0) return out;

    const m = await this.loadManifest(slug, variantId);
    const core = await this.coreChunk(slug, variantId, m);

    const byFile = new Map<string, number[]>();
    for (const cp of cps) {
      const g = core.get(cp);
      if (g) {
        out.set(cp, g);
        continue;
      }
      const range = m.ranges.find((r) => cp >= r.start && cp < r.end);
      if (!range) {
        out.set(cp, null);
        continue;
      }
      const list = byFile.get(range.file);
      if (list) list.push(cp);
      else byFile.set(range.file, [cp]);
    }

    await Promise.all(
      [...byFile.entries()].map(async ([file, list]) => {
        try {
          const chunk = await this.rangeChunk(slug, variantId, file);
          for (const cp of list) out.set(cp, chunk.get(cp));
        } catch {
          for (const cp of list) out.set(cp, null);
        }
      }),
    );
    return out;
  }
}
