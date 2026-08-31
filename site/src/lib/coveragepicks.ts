/** Charts listed in the coverage filter dropdown.
 *
 * All 64 charts stuffed into the dropdown would be too long to be usable,
 * so this is a hand-picked short list.
 *
 * Each writing system must keep at least one reference chart that decides
 * the label used for it, otherwise a user could see
 * "Traditional Chinese (incomplete)" with no consistent chart to filter by.
 * The second reference chart for the same label (Simplified's general-use
 * standard hanzi chart) is omitted for brevity.
 *
 * `test_coverage_picks.py` verifies both of the above.
 */
export const COVERAGE_PICKS: readonly string[] = [
  // Simplified Chinese
  'gb2312',
  'gbk-hanzi',
  'gb18030-2022-l1',
  // Traditional Chinese
  'big5-changyong',
  'big5',
  // Japanese
  'hiragana',
  'katakana',
  'joyo',
  'jisx0208-l1',
  // Korean
  'ksx1001-hangul',
  'hangul-syllables',
  // Latin and European languages
  'latin-basic',
  'latin1-supp',
  'latin-ext-a',
  'viet-latin',
  'wgl4',
  'cyrillic',
  'greek',
  'arabic',
  // Terminal and symbols — a common use case for bitmap fonts
  'box-drawing',
  'block-elements',
  'cp437',
  'powerline',
  'braille',
];
