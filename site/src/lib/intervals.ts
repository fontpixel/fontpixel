/** Glyph-coverage lookup index: per-variant codepoint-range tables for all families, lazy-loaded once.
 * Binary format (inside gzip, little-endian; written by pipeline/opf/emit.py): u32 familyCount;
 * per family: u16 slugLen + utf8 slug, u16 setCount, setCount × (u32 runCount, runCount ×
 * (u32 start, u32 end)), u16 variantCount, variantCount × (u16 idLen + utf8 id, u16 set index).
 * Runs are half-open intervals [start, end); variants with identical coverage share a set.
 */

import { gunzip } from './decompress';

interface FamilyRuns {
  sets: Uint32Array[];
  variants: Map<string, number>;
}

function inRuns(arr: Uint32Array, cp: number): boolean {
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

function coversRuns(arr: Uint32Array, text: string): boolean {
  for (const ch of text) {
    if (/\s/.test(ch)) continue;
    if (!inRuns(arr, ch.codePointAt(0)!)) return false;
  }
  return true;
}

export class CoverageIndex {
  private constructor(private readonly families: Map<string, FamilyRuns>) {}

  static parse(buf: ArrayBuffer): CoverageIndex {
    const v = new DataView(buf);
    const dec = new TextDecoder();
    let p = 0;
    const u16 = () => { const n = v.getUint16(p, true); p += 2; return n; };
    const u32 = () => { const n = v.getUint32(p, true); p += 4; return n; };
    const text = () => { const n = u16(); const s = dec.decode(new Uint8Array(buf, p, n)); p += n; return s; };
    const families = new Map<string, FamilyRuns>();
    const count = u32();
    for (let i = 0; i < count; i++) {
      const slug = text();
      const sets: Uint32Array[] = [];
      for (let s = u16(); s > 0; s--) {
        const arr = new Uint32Array(u32() * 2);
        for (let j = 0; j < arr.length; j++) arr[j] = u32();
        sets.push(arr);
      }
      const variants = new Map<string, number>();
      for (let n = u16(); n > 0; n--) {
        const id = text();
        variants.set(id, u16());
      }
      families.set(slug, { sets, variants });
    }
    return new CoverageIndex(families);
  }

  /** Whether any variant of the family has the code point. */
  has(slug: string, cp: number): boolean {
    return this.families.get(slug)?.sets.some((arr) => inRuns(arr, cp)) ?? false;
  }

  /** Whether one variant (any variant, when none is given) has every non-space character. */
  covers(slug: string, text: string, variantId?: string): boolean {
    const fam = this.families.get(slug);
    if (!fam) return false;
    if (variantId === undefined) return fam.sets.some((arr) => coversRuns(arr, text));
    const set = fam.variants.get(variantId);
    return set !== undefined && coversRuns(fam.sets[set]!, text);
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
