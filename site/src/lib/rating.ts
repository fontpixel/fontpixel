/** Fixed catalogue rating: coverage, size and licensed reuse, plus explicit aesthetic preferences. */
import type { FamilyIndex } from './schema';
import { licenseFactor } from './licenserating';
import { RATING_ADJUSTMENTS } from './rating-adjustments';
import { GOOGLE_FONTS_BONUS, GOOGLE_FONTS_FAMILIES } from './google-fonts';

type RatedFont = Pick<FamilyIndex, 'slug' | 'sizes' | 'coverage' | 'coverageSummary'>
  & { license?: Pick<FamilyIndex['license'], 'spdx'> };
type Script = 'zh-hans' | 'zh-hant' | 'ja' | 'ko' | 'latin' | 'cyrillic' | 'greek' | 'arabic' | 'thai';
const CJK: readonly Script[] = ['zh-hans', 'zh-hant', 'ja', 'ko'];
const HAN: readonly Script[] = ['zh-hans', 'zh-hant', 'ja'];
const ALPHABETS: readonly Script[] = ['cyrillic', 'greek', 'arabic', 'thai'];
const clamp = (value: number) => Number.isFinite(value) ? Math.max(0, Math.min(1, value)) : 0;

/** A family offers its best-sized strike; adding weights or duplicate strikes earns no points. */
export function sizeFactor(sizes: readonly number[]): number {
  const valid = sizes.filter(size => Number.isFinite(size) && size > 0);
  if (!valid.length) return 1;
  return Math.max(...valid.map(size => {
    const distance = Math.max(8 - size, size - 16, 0);
    return 1 - 0.12 * distance / (distance + 8);
  }));
}

/** Construct once per catalogue operation; use the same coverage ratios as the filters. */
export function createRater(charsetIds: readonly string[] = []) {
  const indices = new Map(charsetIds.map((id, i) => [id, i]));
  return (font: RatedFont) => {
    const r = (id: string) => {
      const index = indices.get(id);
      return clamp((index === undefined ? undefined : font.coverage[index]) ?? font.coverageSummary[id] ?? 0);
    };
    const kana = Math.min(r('hiragana'), r('katakana'));
    // Same reference sets as coverage/engine.py's script detection. Japanese also
    // credits kana-only fonts, but cannot pass as complete without common kanji.
    const coverage: Record<Script, number> = {
      'zh-hans': Math.max(r('gb2312'), r('tongyong-guifan')),
      'zh-hant': r('big5-changyong'),
      ja: kana >= 0.95 ? 0.7 * r('jisx0208-l1') + 0.3 * kana : 0,
      ko: Math.max(r('ksx1001-hangul'), r('hangul-syllables')),
      latin: r('latin-basic'),
      cyrillic: r('cyrillic'), greek: r('greek'), arabic: r('arabic'), thai: r('thai'),
    };
    // Shared Han is not evidence that a Japanese font promises complete Chinese.
    // Conversely, complete ASCII must not hide gaps in a CJK font's main language.
    const cjkTargets = CJK.filter(script => coverage[script] >= 0.1);
    // Outside CJK, use the strongest alphabet. A Latin font with half a Greek
    // alphabet has gained useful extras, not a new completeness obligation.
    const candidates = cjkTargets.length ? cjkTargets : ['latin' as const, ...ALPHABETS];
    const extendedLatin = (r('latin1-supp') + r('latin-ext-a')) / 2;
    const terminal = Math.min(r('cp437'), r('box-drawing'), r('block-elements'));
    const commonHan = Math.max(coverage['zh-hans'], coverage['zh-hant'], r('jisx0208-l1'));
    // Most supplemental credit belongs to the target script itself, not the
    // number of unrelated scripts a large Unicode font happens to include.
    const depthByScript: Record<Script, number> = {
      'zh-hans': (r('gbk-hanzi') + r('tongyong-guifan')) / 2,
      'zh-hant': r('big5'),
      ja: (r('jisx0208-l2') + r('jisx0213-l3')) / 2,
      ko: r('hangul-syllables'),
      latin: extendedLatin,
      // No separate extended charts exist for these scripts in the catalogue.
      // Use their reference completeness rather than impose another language.
      cyrillic: coverage.cyrillic, greek: coverage.greek,
      arabic: coverage.arabic, thai: coverage.thai,
    };
    const size = sizeFactor(font.sizes);
    const license = licenseFactor(font.license?.spdx);
    const profiles = candidates.map(target => {
      const core = CJK.includes(target) ? Math.sqrt(coverage[target]) : coverage[target];
      const depth = depthByScript[target];
      // At most one point for cross-script support. Adding more languages after
      // one complete extra cannot push a pan-Unicode font ahead of a specialist.
      // Related Han sets and the primary alphabet do not count as extra scripts.
      const language = Math.max(
        target === 'latin' ? 0 : extendedLatin,
        HAN.includes(target) ? 0 : commonHan,
        target === 'ko' ? 0 : coverage.ko,
        ...ALPHABETS.filter(script => script !== target).map(script => coverage[script]),
      );
      const extra = (8 * depth + language + terminal) / 10;
      // Extras cannot rescue an unusable primary script (including symbol-only fonts).
      const score = Math.round(core * (90 + 10 * extra) * size * license * 1e6) / 1e6;
      return { score, target, coverage: coverage[target], core, extra, depth, language, terminal, size, license };
    });
    // Select the strongest complete profile, including its depth bonus. Choosing
    // by core alone could lower the score when more coverage changes the target
    // and hence switches the supplemental reference tables.
    const automatic = profiles.reduce((best, profile) => profile.score > best.score ? profile : best);
    const configured = RATING_ADJUSTMENTS[font.slug];
    const adjustment = typeof configured === 'number' ? configured : 0;
    const googleFontsBonus = GOOGLE_FONTS_FAMILIES.has(font.slug) ? GOOGLE_FONTS_BONUS : 0;
    // Apply once, after automatic scoring. Keep headroom above 100 so a curated
    // bonus still distinguishes otherwise complete fonts instead of clipping.
    const score = Math.round(Math.max(0, automatic.score + adjustment + googleFontsBonus) * 1e6) / 1e6;
    return { ...automatic, automaticScore: automatic.score, adjustment, googleFontsBonus, score };
  };
}

export function ratingOrder<T extends RatedFont>(fonts: readonly T[], charsetIds: readonly string[] = []): T[] {
  const rate = createRater(charsetIds);
  return fonts.map(font => ({ font, score: rate(font).score }))
    .sort((a, b) => b.score - a.score || (a.font.slug < b.font.slug ? -1 : a.font.slug > b.font.slug ? 1 : 0))
    .map(({ font }) => font);
}
