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
  maxWidth?: number;
  ink?: Rgba;
  paper?: Rgba;
  /**
   * 逐字符墨色，下标与 `for (const ch of text)` 的码位序一致（换行符也占位）。
   * 语法高亮用；null/undefined 处回落到 ink。不受 invert 影响——需要反色
   * 语义的模式（代码框、游戏框）本就固定配色、不开反色。
   */
  charColors?: readonly (Rgba | null | undefined)[];
}

export interface RasterResult {
  width: number;
  height: number;
  data: Uint8ClampedArray;
  missing: number[];
  /**
   * 每个像素是否为字形墨迹（1 = 有墨），供「复制点阵」用。
   *
   * 不从 data 的 RGBA 反推：反色、缺字高亮、网格线都会掺进颜色里，
   * 而这里要的是字形本身的点阵。缺字占位框不计入。
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

/** 字体缺这些码位时按空白推进，而不是标成缺字。 */
function isBlank(cp: number): boolean {
  return cp === 0x20 || cp === 0x09 || cp === 0xa0 || cp === 0x3000;
}

interface Placed {
  glyph: DecodedGlyph | null;
  cp: number;
  x: number;
  line: number;
  blank: boolean;
  /** 在原文本中的码位下标，供 charColors 对位 */
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
  // 空白本来就没有墨迹，字体里没有它也不该画成缺字方框——KS X 1001、
  // JIS 一类的 CJK 点阵字体普遍只有全角空格 U+3000，没有半角 U+0020。
  // 宽度优先取全角空格的一半，取不到就退回缺字宽度。
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
  // 行高不能只信字体自报的 ascent/descent：不少点阵字体的字形实际高过
  // FONT_ASCENT（萤火飞六档全是，最多超 2 行），照声明排第一行就会削顶、
  // 后续行会互相叠笔。按本次真正要画的字形取有效上下界，保证每个像素都画得下。
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
    if (!p.glyph && p.blank) continue; // 空白就留白，不画框
    if (!p.glyph) {
      // 缺字：占位虚线框（高 = ascent，宽 = missAdv-1）
      const w = missAdv - 1;
      const top = baseline - font.ascent + 1;
      const bottom = baseline - 1;
      // 缺字一律衬红：虚线框在小字号下与笔画难以分辨，红底才一眼可辨
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
