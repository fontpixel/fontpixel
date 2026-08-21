/** 像素光栅化（契约 C4）：纯函数输出 RGBA 缓冲，paint 负责放大绘制。 */

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
  highlightMissing: boolean;
  maxWidth?: number;
  ink?: Rgba;
  paper?: Rgba;
}

export interface RasterResult {
  width: number;
  height: number;
  data: Uint8ClampedArray;
  missing: number[];
}

export const LINE_GAP = 1;
export const DEFAULT_INK: Rgba = [17, 17, 17, 255];
export const DEFAULT_PAPER: Rgba = [250, 247, 240, 255];
const HIGHLIGHT: Rgba = [195, 39, 43, 64];

export function MISSING_ADVANCE(pixelSize: number): number {
  return Math.round(pixelSize / 2) + 1;
}

interface Placed {
  glyph: DecodedGlyph | null;
  cp: number;
  x: number;
  line: number;
}

export function rasterize(
  text: string,
  glyphs: Map<number, DecodedGlyph | null>,
  font: FontVMetrics,
  opts: RasterOpts,
): RasterResult {
  const ink = opts.invert ? (opts.paper ?? DEFAULT_PAPER) : (opts.ink ?? DEFAULT_INK);
  const paper = opts.invert ? (opts.ink ?? DEFAULT_INK) : (opts.paper ?? DEFAULT_PAPER);
  const lineHeight = font.ascent + font.descent;
  const missAdv = MISSING_ADVANCE(font.pixelSize);

  const placed: Placed[] = [];
  const missing: number[] = [];
  let line = 0;
  let x = 0;
  let maxLineWidth = 1;
  for (const ch of text) {
    if (ch === '\n') {
      line += 1;
      x = 0;
      continue;
    }
    const cp = ch.codePointAt(0)!;
    const g = glyphs.get(cp) ?? null;
    const adv = g ? Math.max(g.dwidth, 0) : missAdv;
    if (opts.maxWidth && x > 0 && x + adv > opts.maxWidth) {
      line += 1;
      x = 0;
    }
    if (!g) missing.push(cp);
    placed.push({ glyph: g, cp, x, line });
    x += adv;
    if (x > maxLineWidth) maxLineWidth = x;
  }

  const lines = line + 1;
  const width = Math.max(1, maxLineWidth);
  const height = lines * lineHeight + (lines - 1) * LINE_GAP;
  const data = new Uint8ClampedArray(width * height * 4);
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
    const baseline = p.line * (lineHeight + LINE_GAP) + font.ascent;
    if (!p.glyph) {
      // 缺字：占位虚线框（高 = ascent，宽 = missAdv-1）
      const w = missAdv - 1;
      const top = baseline - font.ascent + 1;
      const bottom = baseline - 1;
      if (opts.highlightMissing) {
        for (let yy = top; yy <= bottom; yy++)
          for (let xx = p.x; xx < p.x + w; xx++) put(xx, yy, HIGHLIGHT);
      }
      for (let xx = p.x; xx < p.x + w; xx += 2) {
        put(xx, top, ink);
        put(xx, bottom, ink);
      }
      for (let yy = top; yy <= bottom; yy += 2) {
        put(p.x, yy, ink);
        put(p.x + w - 1, yy, ink);
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
          put(p.x + g.xoff + xx, top + yy, ink);
        }
      }
    }
  }

  return { width, height, data, missing };
}

/** 把光栅结果按整数倍绘制到 canvas;grid 在 scale≥4 时叠加网格线。 */
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
