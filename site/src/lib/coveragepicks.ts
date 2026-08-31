/** 覆盖率筛选下拉里列出的字表。
 *
 * 全部 64 张字表塞进下拉太长也没法用，这里是一份人工挑选的短名单。
 *
 * 每种书写系统至少要留一张判定该标签所用的参照字表，否则用户看得到
 * “Traditional Chinese (incomplete)” 却没法按同一把尺子去筛。至于同一
 * 标签的第二张参照表（简体的通用规范汉字表）为求简短已略去。
 *
 * `test_coverage_picks.py` 会校验以上两点。
 */
export const COVERAGE_PICKS: readonly string[] = [
  // 简体中文
  'gb2312',
  'gbk-hanzi',
  'gb18030-2022-l1',
  // 繁体中文
  'big5-changyong',
  'big5',
  // 日文
  'hiragana',
  'katakana',
  'joyo',
  'jisx0208-l1',
  // 韩文
  'ksx1001-hangul',
  'hangul-syllables',
  // 拉丁与欧洲语言
  'latin-basic',
  'latin1-supp',
  'latin-ext-a',
  'viet-latin',
  'wgl4',
  'cyrillic',
  'greek-coptic',
  // 终端与符号——点阵字体的常见用途
  'box-drawing',
  'block-elements',
  'cp437',
  'powerline',
  'braille',
];
