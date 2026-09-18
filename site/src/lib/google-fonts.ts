/** Catalogue families on Google Fonts, including grouped families and those
 * whose homepage points to their author. Keep this reviewed list in sync with
 * family.toml metadata; rating.test.ts checks the homepage-based entries. */
export const GOOGLE_FONTS_FAMILIES: ReadonlySet<string> = new Set([
  'bitcount',
  'bytesized',
  'dotgothic16',
  'doto',
  'handjet',
  'jacquard',
  'jacquarda-bastarda-9',
  'jersey',
  'micro-5',
  'pixelify-sans',
  'press-start-2p',
  'silkscreen',
  'tiny5',
]);

export const GOOGLE_FONTS_BONUS = 1;
