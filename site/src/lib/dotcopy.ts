/** 把试写框里的点阵导出成可粘贴的文本。 */
import type { DecodedGlyph } from './glyphpack';
import { rowBytes } from './glyphpack';
import type { RasterResult } from './render';

/** 整段渲染结果转成 `.#` 点阵图。 */
export function toDotText(r: RasterResult): string {
  const lines: string[] = [];
  for (let y = 0; y < r.height; y++) {
    let s = '';
    for (let x = 0; x < r.width; x++) s += r.mask[y * r.width + x] ? '#' : '.';
    lines.push(s);
  }
  // 去掉上下全空的行，粘出去才不会带一堆空白
  let a = 0;
  let b = lines.length - 1;
  while (a <= b && !lines[a]!.includes('#')) a++;
  while (b >= a && !lines[b]!.includes('#')) b--;
  return lines.slice(a, b + 1).join('\n');
}

function hexRows(g: DecodedGlyph): string[] {
  const nb = rowBytes(g.w);
  const out: string[] = [];
  for (let y = 0; y < g.h; y++) {
    let s = '';
    for (let i = 0; i < nb; i++) {
      s += (g.rows[y * nb + i] ?? 0).toString(16).toUpperCase().padStart(2, '0');
    }
    out.push(s);
  }
  return out;
}

/**
 * 按 BDF 的字形段格式导出，每个字符一段。
 *
 * 不是整幅画面导成一个巨大字形——那样粘回字体里没用。这里给的是可以直接
 * 贴进 .bdf 的 STARTCHAR…ENDCHAR 段，编码、步进、包围盒、位图行都按 BDF
 * 的写法（位图每行按字节对齐、高位在左，与 BDF 规范一致）。
 */
export function toBdfText(
  text: string,
  glyphs: Map<number, DecodedGlyph | null>,
): string {
  const seen = new Set<number>();
  const out: string[] = [];
  for (const ch of text) {
    const cp = ch.codePointAt(0)!;
    if (ch === '\n' || seen.has(cp)) continue;
    seen.add(cp);
    const g = glyphs.get(cp);
    if (!g) continue;
    const name = `U+${cp.toString(16).toUpperCase().padStart(4, '0')}`;
    out.push(
      `STARTCHAR ${name}`,
      `ENCODING ${cp}`,
      'SWIDTH 0 0',
      `DWIDTH ${g.dwidth} 0`,
      `BBX ${g.w} ${g.h} ${g.xoff} ${g.yoff}`,
      'BITMAP',
      ...hexRows(g),
      'ENDCHAR',
    );
  }
  return out.join('\n');
}
