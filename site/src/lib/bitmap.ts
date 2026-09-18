/** In-memory BDF glyphs, not a separately published font format. */
export interface DecodedGlyph {
  cp: number;
  dwidth: number;
  w: number;
  h: number;
  xoff: number;
  yoff: number;
  rows: Uint8Array;
}
export const rowBytes = (width: number) => Math.ceil(width / 8);
export interface BitmapFont {
  pixelSize: number;
  ascent: number;
  descent: number;
  glyphCount: number;
  glyphs: Map<number, DecodedGlyph>;
  ranges: { start: number; end: number; glyphs: number }[];
}
