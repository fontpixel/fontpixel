import { Font } from 'bdfparser';
import { gunzip } from './decompress';
import { rowBytes, type BitmapFont, type DecodedGlyph } from './bitmap';

/** Downloadable BDFs are normalized to Unicode by the build pipeline. */
export async function decodeBdf(buffer: ArrayBuffer): Promise<BitmapFont> {
  const text = new TextDecoder('latin1').decode(await gunzip(buffer));
  if (!text.startsWith('STARTFONT')) throw new Error('Invalid BDF download');
  async function* lines() {
    let start = 0;
    for (let end = text.indexOf('\n'); end !== -1; end = text.indexOf('\n', start)) {
      yield text.slice(start, end).replace(/\r$/, '');
      start = end + 1;
    }
    if (start < text.length) yield text.slice(start);
  }
  const font = await new Font().load_filelines(lines());
  const encoded = [...font.glyphs].filter(([cp]) => cp >= 0 && cp <= 0x10ffff).sort((a, b) => a[0] - b[0]);
  const storage = new Uint8Array(encoded.reduce((n, [, g]) => n + rowBytes(g[2]) * g[3], 0));
  const glyphs = new Map<number, DecodedGlyph>();
  const blocks = new Map<number, number>();
  let offset = 0;
  for (const [cp, g] of encoded) {
    const stride = rowBytes(g[2]);
    const rows = storage.subarray(offset, offset + stride * g[3]);
    offset += rows.length;
    for (let y = 0; y < g[3]; y++) {
      const hex = g[16][y] ?? '';
      for (let x = 0; x < stride; x++) rows[y * stride + x] = parseInt(hex.slice(x * 2, x * 2 + 2) || '00', 16);
    }
    glyphs.set(cp, { cp, w: g[2], h: g[3], xoff: g[4], yoff: g[5], dwidth: g[8] ?? 0, rows });
    const block = Math.floor(cp / 256) * 256;
    blocks.set(block, (blocks.get(block) ?? 0) + 1);
  }
  return {
    pixelSize: Number(font.props.pixel_size ?? font.headers?.fbby ?? 16),
    ascent: Number(font.props.font_ascent ?? 0),
    descent: Number(font.props.font_descent ?? 0),
    glyphCount: glyphs.size, glyphs,
    ranges: [...blocks].map(([start, count]) => ({ start, end: start + 256, glyphs: count })),
  };
}
