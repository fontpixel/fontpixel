/** Glyph-coverage lookup index: codepoint-range table for all families, lazy-loaded once.
 * Binary format (inside gzip): u32 familyCount; per family: u16 slugLen + utf8 slug,
 * u32 runCount, runCount × (u32 start, u32 end) — half-open interval [start, end).
 */

import { gunzip } from './decompress';

export class CoverageIndex {
  private constructor(private readonly runs: Map<string, Uint32Array>) {}

  static parse(buf: ArrayBuffer): CoverageIndex {
    const v = new DataView(buf);
    const dec = new TextDecoder();
    let p = 0;
    const count = v.getUint32(p, true);
    p += 4;
    const runs = new Map<string, Uint32Array>();
    for (let i = 0; i < count; i++) {
      const slugLen = v.getUint16(p, true);
      p += 2;
      const slug = dec.decode(new Uint8Array(buf, p, slugLen));
      p += slugLen;
      const n = v.getUint32(p, true);
      p += 4;
      const arr = new Uint32Array(n * 2);
      for (let j = 0; j < n * 2; j++) {
        arr[j] = v.getUint32(p, true);
        p += 4;
      }
      runs.set(slug, arr);
    }
    return new CoverageIndex(runs);
  }

  has(slug: string, cp: number): boolean {
    const arr = this.runs.get(slug);
    if (!arr) return false;
    let lo = 0;
    let hi = arr.length / 2 - 1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      const start = arr[mid * 2]!;
      const end = arr[mid * 2 + 1]!;
      if (cp < start) hi = mid - 1;
      else if (cp >= end) lo = mid + 1;
      else return true;
    }
    return false;
  }

  covers(slug: string, text: string): boolean {
    for (const ch of text) {
      if (/\s/.test(ch)) continue;
      if (!this.has(slug, ch.codePointAt(0)!)) return false;
    }
    return true;
  }
}

let cached: Promise<CoverageIndex> | null = null;

export function loadCoverageIndex(
  dataBase: string,
  fetchFn: typeof fetch = (input, init) => globalThis.fetch(input, init),
): Promise<CoverageIndex> {
  if (!cached) {
    cached = (async () => {
      const res = await fetchFn(`${dataBase}/coverage-intervals.bin.gz`);
      if (!res.ok) throw new Error(`coverage index: ${res.status}`);
      return CoverageIndex.parse(await gunzip(await res.arrayBuffer()));
    })();
    cached.catch(() => (cached = null));
  }
  return cached;
}
