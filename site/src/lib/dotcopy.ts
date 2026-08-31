/** Export the bitmap in the trial-writing box as pasteable text. */
import type { DecodedGlyph } from './glyphpack';
import { rowBytes } from './glyphpack';
import type { RasterResult } from './render';

/** Convert a full raster result into a `.#` bitmap. */
export function toDotText(r: RasterResult): string {
  const lines: string[] = [];
  for (let y = 0; y < r.height; y++) {
    let s = '';
    for (let x = 0; x < r.width; x++) s += r.mask[y * r.width + x] ? '#' : '.';
    lines.push(s);
  }
  // Trim blank rows from the top and bottom so pasting doesn't drag in whitespace
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
 * Export in BDF glyph-block format, one block per character.
 *
 * This does not export the whole rendered canvas as one giant glyph — that
 * wouldn't be usable when pasted back into a font. Instead it produces
 * STARTCHAR…ENDCHAR blocks that can be pasted directly into a .bdf file,
 * with encoding, step width, bounding box, and bitmap rows all following
 * BDF conventions (each bitmap row byte-aligned, MSB first, matching the
 * BDF spec).
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
