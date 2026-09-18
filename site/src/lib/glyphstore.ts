/** The font download is also the rendering source. Cache whole selected variants. */
import type { BitmapFont, DecodedGlyph } from './bitmap';

let worker: Worker | undefined;
let requestId = 0;
const pending = new Map<number, { resolve: (font: BitmapFont) => void; reject: (e: Error) => void }>();
async function parse(buffer: ArrayBuffer): Promise<BitmapFont> {
  if (typeof Worker === 'undefined') return (await import('./bdf')).decodeBdf(buffer);
  if (!worker) {
    worker = new Worker(new URL('./bdf.worker.ts', import.meta.url), { type: 'module' });
    worker.onmessage = ({ data }) => {
      const job = pending.get(data.id);
      pending.delete(data.id);
      if (data.error) job?.reject(new Error(data.error));
      else job?.resolve(data.font);
    };
    worker.onerror = (event) => {
      for (const job of pending.values()) job.reject(new Error(event.message));
      pending.clear();
      worker?.terminate();
      worker = undefined;
    };
  }
  const id = ++requestId;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    worker!.postMessage({ id, buffer }, [buffer]);
  });
}

export class GlyphStore {
  private fonts = new Map<string, Promise<BitmapFont>>();
  private inflight = new Map<string, Promise<BitmapFont>>();
  private readonly fetchFn: typeof fetch;
  private readonly downloadBase: string;
  constructor(dataBase: string, fetchFn?: typeof fetch, private readonly capacity = 8) {
    this.fetchFn = fetchFn ?? ((input, init) => globalThis.fetch(input, init));
    this.downloadBase = dataBase.replace(/\/data\/?$/, '/downloads');
  }
  loadFont(slug: string, variantId: string): Promise<BitmapFont> {
    const key = `${slug}/${variantId}`;
    const cached = this.fonts.get(key) ?? this.inflight.get(key);
    if (cached) {
      if (this.fonts.has(key)) {
        this.fonts.delete(key);
        this.fonts.set(key, cached);
      }
      return cached;
    }
    const url = `${this.downloadBase}/${encodeURIComponent(`${slug}--${variantId}.bdf.gz`)}`;
    const promise = this.fetchFn(url).then(async (response) => {
      if (!response.ok) throw new Error(`BDF ${url}: ${response.status}`);
      return parse(await response.arrayBuffer());
    });
    this.inflight.set(key, promise);
    void promise.then(() => {
      this.inflight.delete(key);
      this.fonts.set(key, promise);
      while (this.fonts.size > this.capacity) this.fonts.delete(this.fonts.keys().next().value!);
    }, () => { this.inflight.delete(key); });
    return promise;
  }
  async glyphsFor(slug: string, variantId: string, text: string): Promise<Map<number, DecodedGlyph | null>> {
    if (!text) return new Map();
    const font = await this.loadFont(slug, variantId);
    return new Map([...text].filter((ch) => ch !== '\n').map((ch) => {
      const cp = ch.codePointAt(0)!;
      return [cp, font.glyphs.get(cp) ?? null];
    }));
  }
}
const stores = new Map<string, GlyphStore>();
export function getGlyphStore(dataBase: string): GlyphStore {
  let store = stores.get(dataBase);
  if (!store) stores.set(dataBase, store = new GlyphStore(dataBase));
  return store;
}
