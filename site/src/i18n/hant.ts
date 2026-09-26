/** Simplified → Traditional (Taiwan usage) conversion.
 *
 * Traditional Chinese isn't a different language, it's the same language with
 * a different glyph set and vocabulary, so we run it through OpenCC conversion
 * rather than translation: edit a sentence in Chinese and the Traditional
 * version automatically follows — there's never a risk of the two texts
 * drifting out of sync.
 *
 * We use s2twp (Taiwan characters + vocabulary substitution) rather than the
 * glyph-only s2t — the latter leaves Mainland words like 軟件/信息 in place,
 * which reads as obviously machine-converted at a glance. The tradeoff is
 * that s2twp occasionally mis-converts specialized compound terms, which
 * FIXUPS corrects.
 *
 * Conversion happens at build time (this site is fully static) and is cached
 * per unique string; a full site build converts roughly a thousand strings,
 * at millisecond cost.
 */
import * as OpenCC from 'opencc-js';

const convert = OpenCC.Converter({ from: 'cn', to: 'twp' });

/** Words s2twp gets wrong; corrected here after conversion. */
const FIXUPS: [RegExp, string][] = [
  // s2twp treats 位图 as a standalone word and converts it to 點陣圖 (bitmap
  // image), but on this site 位图 always means a bitmap font/strike, which
  // Taiwan usage calls 點陣. All six occurrences on the site have been checked.
  [/點陣圖/g, '點陣'],
  // Taiwan usage prefers 授權 over 許可證
  [/許可證/g, '授權'],
  // The Traditional site name is a fixed value (see the zh-Hant key in
  // sitenames.json), not the output of literal conversion; this rule also
  // fixes up the site name wherever it's embedded in a sentence (e.g. the
  // about-page intro).
  [/開源畫素字型館/g, '開源點陣字型館'],
  // Keep the font term 像素 instead of s2twp's image-oriented 畫素.
  [/畫素/g, '像素'],
  // Simplified body text uses curly quotes “” uniformly; Traditional (Taiwan)
  // convention is corner brackets 「」, so convert them back. Same for inner
  // quotes: ''→『』. OpenCC only handles characters and words, not punctuation.
  [/‘([^’]*)’/g, '『$1』'],
  [/“([^”]*)”/g, '「$1」'],
];

/** Whole-string overrides: a few copy items have a Traditional version that's
 * written separately rather than converted from the Simplified version.
 *
 * For example the site description — the keyword mix Traditional readers
 * search with differs from Simplified (using 點陣/像素/畫素/位元圖 together); this
 * kind of SEO-driven difference is something OpenCC can't produce, and
 * shouldn't be forced through FIXUPS either (that's word-by-word replacement
 * and would collateral-damage other text). The key is the Simplified source
 * text, the value is the final Traditional text.
 */
const OVERRIDES: Record<string, string> = {
  // The example names exact code points, so keep 𰻝 instead of converting it to 𰻞.
  '输入任意字符，如：Æφは𰻝': '輸入任意字元，如：Æφは𰻝',
  // This keyword list intentionally keeps 畫素 as an exception to FIXUPS.
  '免费可商用的自由开源点阵/像素/位图字体合集与工具，BDF、PCF、TTF格式下载':
    '免費可商用的自由開源點陣/像素/畫素/位元圖字型合集與工具，BDF、PCF、TTF格式下載',
  // "Follow" on GitHub is 追蹤 in Taiwan; OpenCC keeps the mainland 關注.
  '关注@tomchen': '追蹤@tomchen',
};

const cache = new Map<string, string>();

/** Convert a piece of Simplified Chinese to Traditional; non-Chinese content is returned unchanged. */
export function toHant(text: string): string {
  if (!text) return text;
  const hit = cache.get(text);
  if (hit !== undefined) return hit;
  const override = OVERRIDES[text];
  if (override !== undefined) {
    cache.set(text, override);
    return override;
  }
  let out = convert(text);
  for (const [re, to] of FIXUPS) out = out.replace(re, to);
  cache.set(text, out);
  return out;
}

/** Deep-convert a structure containing only strings and nested objects (used for the whole UI strings set). */
export function toHantDeep<T>(value: T): T {
  if (typeof value === 'string') return toHant(value) as unknown as T;
  if (Array.isArray(value)) return value.map(toHantDeep) as unknown as T;
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) out[k] = toHantDeep(v);
    return out as T;
  }
  return value;
}
