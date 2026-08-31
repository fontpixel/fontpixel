/** Pixel rasterization (contract C4): a pure function that outputs an RGBA buffer; paint handles scaled drawing. */

import type { DecodedGlyph } from './glyphpack';
import { rowBytes } from './glyphpack';

export interface FontVMetrics {
  pixelSize: number;
  ascent: number;
  descent: number;
}

export type Rgba = readonly [number, number, number, number];

export interface RasterOpts {
  invert: boolean;
  maxWidth?: number;
  ink?: Rgba;
  paper?: Rgba;
  /**
   * Per-character ink color, indices matching the codepoint order of
   * `for (const ch of text)` (newlines occupy a slot too). Used for syntax
   * highlighting; falls back to `ink` where null/undefined. Not affected by
   * invert — modes that need fixed color semantics (code box, game box)
   * already use a fixed palette and never enable invert.
   */
  charColors?: readonly (Rgba | null | undefined)[];
}

export interface RasterResult {
  width: number;
  height: number;
  data: Uint8ClampedArray;
  missing: number[];
  /**
   * Whether each pixel is glyph ink (1 = ink), used by "copy bitmap".
   *
   * This isn't derived back from `data`'s RGBA: invert, missing-glyph
   * highlighting, and grid lines all get mixed into the color, but what's
   * wanted here is the glyph's own bitmap. The missing-glyph placeholder box
   * is not counted.
   */
  mask: Uint8Array;
}

export const LINE_GAP = 1;
export const DEFAULT_INK: Rgba = [17, 17, 17, 255];
export const DEFAULT_PAPER: Rgba = [250, 247, 240, 255];
const HIGHLIGHT: Rgba = [195, 39, 43, 64];

export function MISSING_ADVANCE(pixelSize: number): number {
  return Math.round(pixelSize / 2) + 1;
}

/** When the font lacks these codepoints, advance as whitespace instead of marking them missing. */
function isBlank(cp: number): boolean {
  return cp === 0x20 || cp === 0x09 || cp === 0xa0 || cp === 0x3000;
}

interface Placed {
  glyph: DecodedGlyph | null;
  cp: number;
  x: number;
  line: number;
  blank: boolean;
  /** Codepoint index in the original text, for aligning with charColors */
  idx: number;
}

export function rasterize(
  text: string,
  glyphs: Map<number, DecodedGlyph | null>,
  font: FontVMetrics,
  opts: RasterOpts,
): RasterResult {
  const ink = opts.invert ? (opts.paper ?? DEFAULT_PAPER) : (opts.ink ?? DEFAULT_INK);
  const paper = opts.invert ? (opts.ink ?? DEFAULT_INK) : (opts.paper ?? DEFAULT_PAPER);
  const missAdv = MISSING_ADVANCE(font.pixelSize);
  // Whitespace has no ink to begin with, so a font missing it shouldn't be
  // drawn as a missing-glyph box — CJK bitmap fonts like KS X 1001 and JIS
  // typically only have the full-width space U+3000, not the half-width
  // U+0020. Prefer half the full-width space's advance for the width,
  // falling back to the missing-glyph width if unavailable.
  const fullWidthSpace = glyphs.get(0x3000);
  const spaceAdv = fullWidthSpace
    ? Math.max(1, Math.round(Math.max(fullWidthSpace.dwidth, 0) / 2))
    : missAdv;

  const placed: Placed[] = [];
  const missing: number[] = [];
  let line = 0;
  let x = 0;
  let maxLineWidth = 1;
  let idx = -1;
  for (const ch of text) {
    idx += 1;
    if (ch === '\n') {
      line += 1;
      x = 0;
      continue;
    }
    const cp = ch.codePointAt(0)!;
    const g = glyphs.get(cp) ?? null;
    const blank = !g && isBlank(cp);
    const adv = g ? Math.max(g.dwidth, 0) : blank ? spaceAdv : missAdv;
    if (opts.maxWidth && x > 0 && x + adv > opts.maxWidth) {
      line += 1;
      x = 0;
    }
    if (!g && !blank) missing.push(cp);
    placed.push({ glyph: g, cp, x, line, blank, idx });
    x += adv;
    if (x > maxLineWidth) maxLineWidth = x;
  }

  const lines = line + 1;
  const width = Math.max(1, maxLineWidth);
  // Line height can't just trust the font's self-reported ascent/descent:
  // many bitmap fonts have glyphs taller than FONT_ASCENT (true of all six
  // Firefly sizes, by up to 2 rows) — laying out the first line by the
  // declared metrics would clip the top, and later lines would overlap.
  // Compute the actual effective bounds from the glyphs being drawn this
  // time, so every pixel fits.
  let above = font.ascent;
  let below = font.descent;
  for (const p of placed) {
    if (!p.glyph) continue;
    above = Math.max(above, p.glyph.yoff + p.glyph.h);
    below = Math.max(below, -p.glyph.yoff);
  }
  const lineHeight = above + below;
  const height = lines * lineHeight + (lines - 1) * LINE_GAP;
  const data = new Uint8ClampedArray(width * height * 4);
  const mask = new Uint8Array(width * height);
  for (let i = 0; i < width * height; i++) {
    data[i * 4] = paper[0];
    data[i * 4 + 1] = paper[1];
    data[i * 4 + 2] = paper[2];
    data[i * 4 + 3] = paper[3];
  }

  const put = (px: number, py: number, c: Rgba) => {
    if (px < 0 || py < 0 || px >= width || py >= height) return;
    const i = (py * width + px) * 4;
    if (c[3] === 255) {
      data[i] = c[0];
      data[i + 1] = c[1];
      data[i + 2] = c[2];
      data[i + 3] = 255;
    } else {
      const a = c[3] / 255;
      data[i] = Math.round(c[0] * a + data[i]! * (1 - a));
      data[i + 1] = Math.round(c[1] * a + data[i + 1]! * (1 - a));
      data[i + 2] = Math.round(c[2] * a + data[i + 2]! * (1 - a));
      data[i + 3] = 255;
    }
  };

  for (const p of placed) {
    const baseline = p.line * (lineHeight + LINE_GAP) + above;
    const inkC = opts.charColors?.[p.idx] ?? ink;
    if (!p.glyph && p.blank) continue; // blank stays blank, no box drawn
    if (!p.glyph) {
      // missing glyph: placeholder dashed box (height = ascent, width = missAdv-1)
      const w = missAdv - 1;
      const top = baseline - font.ascent + 1;
      const bottom = baseline - 1;
      // Always tint missing glyphs red: at small sizes a dashed box is hard to tell from actual strokes, a red backing makes it instantly recognizable
      for (let yy = top; yy <= bottom; yy++)
        for (let xx = p.x; xx < p.x + w; xx++) put(xx, yy, HIGHLIGHT);
      for (let xx = p.x; xx < p.x + w; xx += 2) {
        put(xx, top, inkC);
        put(xx, bottom, inkC);
      }
      for (let yy = top; yy <= bottom; yy += 2) {
        put(p.x, yy, inkC);
        put(p.x + w - 1, yy, inkC);
      }
      continue;
    }
    const g = p.glyph;
    const nb = rowBytes(g.w);
    const top = baseline - (g.yoff + g.h);
    for (let yy = 0; yy < g.h; yy++) {
      for (let xx = 0; xx < g.w; xx++) {
        const b = g.rows[yy * nb + (xx >> 3)]!;
        if (b & (0x80 >> (xx & 7))) {
          const px = p.x + g.xoff + xx;
          const py = top + yy;
          put(px, py, inkC);
          if (px >= 0 && py >= 0 && px < width && py < height) {
            mask[py * width + px] = 1;
          }
        }
      }
    }
  }

  return { width, height, data, missing, mask };
}

/** Draw the raster result onto a canvas at an integer scale; grid overlays gridlines when scale≥4. */
export function paint(
  canvas: HTMLCanvasElement,
  r: RasterResult,
  scale: number,
  opts?: { grid?: boolean; gridColor?: string },
): void {
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  canvas.width = r.width * scale;
  canvas.height = r.height * scale;
  const img = new ImageData(new Uint8ClampedArray(r.data), r.width, r.height);
  if (scale === 1) {
    ctx.putImageData(img, 0, 0);
  } else {
    const off = document.createElement('canvas');
    off.width = r.width;
    off.height = r.height;
    off.getContext('2d')!.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(off, 0, 0, r.width * scale, r.height * scale);
  }
  if (opts?.grid && scale >= 4) {
    ctx.strokeStyle = opts.gridColor ?? 'rgba(128,128,128,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = 0; x <= r.width; x++) {
      ctx.moveTo(x * scale + 0.5, 0);
      ctx.lineTo(x * scale + 0.5, r.height * scale);
    }
    for (let y = 0; y <= r.height; y++) {
      ctx.moveTo(0, y * scale + 0.5);
      ctx.lineTo(r.width * scale, y * scale + 0.5);
    }
    ctx.stroke();
  }
}
