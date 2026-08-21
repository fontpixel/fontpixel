/** 字形包 v1 解码器（契约 C1/C4）。与 pipeline/pfc/glyphpack.py 互为镜像。 */

export interface DecodedGlyph {
  cp: number;
  dwidth: number;
  w: number;
  h: number;
  xoff: number;
  yoff: number;
  /** h × ceil(w/8) 字节，行序自上而下，位 MSB-first */
  rows: Uint8Array;
}

const HEADER_SIZE = 16;
const ENTRY_SIZE = 14;

export function rowBytes(w: number): number {
  return (w + 7) >> 3;
}

export class GlyphChunk {
  private constructor(
    private readonly view: DataView,
    private readonly cps: Uint32Array,
    private readonly bitmapBase: number,
    readonly rangeStart: number,
    readonly rangeEnd: number,
  ) {}

  static parse(buf: ArrayBuffer): GlyphChunk {
    const view = new DataView(buf);
    if (buf.byteLength < HEADER_SIZE) throw new Error('chunk too small');
    const magic =
      String.fromCharCode(view.getUint8(0), view.getUint8(1), view.getUint8(2), view.getUint8(3));
    if (magic !== 'PFG1') throw new Error(`bad magic ${magic}`);
    const version = view.getUint8(4);
    if (version !== 1) throw new Error(`unsupported version ${version}`);
    const count = view.getUint16(6, true);
    const rangeStart = view.getUint32(8, true);
    const rangeEnd = view.getUint32(12, true);
    const cps = new Uint32Array(count);
    for (let i = 0; i < count; i++) {
      cps[i] = view.getUint32(HEADER_SIZE + i * ENTRY_SIZE, true);
    }
    return new GlyphChunk(view, cps, HEADER_SIZE + count * ENTRY_SIZE, rangeStart, rangeEnd);
  }

  get size(): number {
    return this.cps.length;
  }

  private indexOf(cp: number): number {
    let lo = 0;
    let hi = this.cps.length - 1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      const v = this.cps[mid]!;
      if (v === cp) return mid;
      if (v < cp) lo = mid + 1;
      else hi = mid - 1;
    }
    return -1;
  }

  has(cp: number): boolean {
    return this.indexOf(cp) >= 0;
  }

  get(cp: number): DecodedGlyph | null {
    const i = this.indexOf(cp);
    if (i < 0) return null;
    const off = HEADER_SIZE + i * ENTRY_SIZE;
    const v = this.view;
    const dwidth = v.getInt16(off + 4, true);
    const w = v.getUint8(off + 6);
    const h = v.getUint8(off + 7);
    const xoff = v.getInt8(off + 8);
    const yoff = v.getInt8(off + 9);
    const bitmapOffset = v.getUint32(off + 10, true);
    const size = h * rowBytes(w);
    const rows = new Uint8Array(this.view.buffer, this.bitmapBase + bitmapOffset, size);
    return { cp, dwidth, w, h, xoff, yoff, rows };
  }
}
