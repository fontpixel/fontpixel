import sitenames from './sitenames.json';
import type { Lang, UIStrings } from './types';
import { zh } from './zh';
import { en } from './en';
import { ja } from './ja';
import { ko } from './ko';
import { fr } from './fr';
import { toHant, toHantDeep } from './hant';

/** Languages the site supports, in the order the language menu shows them. */
export const LANGS: Lang[] = ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr'];

/** Each language's name for itself, shown in the menu in its own script. */
export const LANG_NAMES: Record<Lang, string> = {
  zh: '简体中文',
  'zh-Hant': '繁體中文',
  en: 'English',
  ja: '日本語',
  ko: '한국어',
  fr: 'Français',
};

/** BCP 47 tags used for hreflang. */
export const LANG_TAGS: Record<Lang, string> = {
  zh: 'zh-Hans',
  'zh-Hant': 'zh-Hant',
  en: 'en',
  ja: 'ja',
  ko: 'ko',
  fr: 'fr',
};

// Traditional Chinese isn't translated, it's converted — the whole set is derived from Simplified at build time
let hant: UIStrings | null = null;

export function t(lang: string): UIStrings {
  switch (lang) {
    case 'zh':
      return zh;
    case 'zh-Hant':
      // The site name is a fixed value, not a conversion output: the Traditional version comes from the zh-Hant key in sitenames.json
      return (hant ??= { ...toHantDeep(zh), siteName: sitenames['zh-Hant'] });
    case 'ja':
      return ja;
    case 'ko':
      return ko;
    case 'fr':
      return fr;
    default:
      return en;
  }
}

/** Per-language priority order for picking a font name; falls back down the list, ending at family.name. */
const NAME_FALLBACK: Record<Lang, string[]> = {
  en: ['en'],
  // Chinese UI falls back to the Japanese name rather than the Latin one: Han names like 東雲ゴシック are recognizable to Chinese readers
  zh: ['zh-Hans', 'ja'],
  'zh-Hant': ['zh-Hant', 'zh-Hans', 'ja'],
  ja: ['ja', 'en'],
  ko: ['ko', 'en'],
  fr: ['fr', 'en'],
};

/**
 * Pick a font name for the current UI language.
 *
 * `names` only has entries for languages the author actually named the font in;
 * a missing zh-Hant is derived from Simplified via OpenCC, same as any other
 * Chinese text on the site. If nothing matches, fall back to `fallback`
 * (family.name, usually the Latin name).
 */
export function pickName(
  lang: string,
  names: Record<string, string>,
  fallback: string,
): string {
  for (const key of NAME_FALLBACK[lang as Lang] ?? ['en']) {
    const v = names[key];
    if (!v) continue;
    // Fall back to converting Simplified when Traditional is missing, but never convert Japanese names — that's Japanese, not Chinese
    return lang === 'zh-Hant' && key === 'zh-Hans' ? toHant(v) : v;
  }
  return fallback;
}

/**
 * Get a piece of text that varies by language.
 *
 * Font metadata only exists in Chinese and English: Traditional is derived
 * from Simplified, and every other language falls back to English — a rule
 * set from the start of the collection so that adding a new language never
 * requires going back and writing blurbs for 130 families.
 */
export function pickText(lang: string, zhText: string, enText: string): string {
  if (lang === 'zh') return zhText || enText;
  if (lang === 'zh-Hant') return zhText ? toHant(zhText) : enText;
  return enText || zhText;
}

/**
 * The "primary alternate language": Chinese variants go to English, everything
 * else goes to Simplified Chinese.
 *
 * With six languages shown in a menu, there's no longer a single "other
 * language"; this function is only used to highlight the option most likely
 * to be clicked (and is also what end-to-end tests target).
 */
export function otherLang(lang: string): Lang {
  return lang === 'zh' || lang === 'zh-Hant' ? 'en' : 'zh';
}

export { toHant };
export type { Lang, UIStrings };
