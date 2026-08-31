import sitenames from './sitenames.json';
import type { Lang, UIStrings } from './types';
import { zh } from './zh';
import { en } from './en';
import { ja } from './ja';
import { ko } from './ko';
import { fr } from './fr';
import { toHant, toHantDeep } from './hant';

/** 站点支持的语言，顺序即语言菜单的顺序。 */
export const LANGS: Lang[] = ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr'];

/** 语言的自称，菜单里按各自语言显示。 */
export const LANG_NAMES: Record<Lang, string> = {
  zh: '简体中文',
  'zh-Hant': '繁體中文',
  en: 'English',
  ja: '日本語',
  ko: '한국어',
  fr: 'Français',
};

/** hreflang 用的 BCP 47 标签。 */
export const LANG_TAGS: Record<Lang, string> = {
  zh: 'zh-Hans',
  'zh-Hant': 'zh-Hant',
  en: 'en',
  ja: 'ja',
  ko: 'ko',
  fr: 'fr',
};

// 繁体不是翻译而是转换，构建期由简体整份转出
let hant: UIStrings | null = null;

export function t(lang: string): UIStrings {
  switch (lang) {
    case 'zh':
      return zh;
    case 'zh-Hant':
      // 站名是定名不是转换产物：繁体版取 sitenames.json 的 zh-Hant 键
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

/** 各语言取字体名的顺序；找不到就往后退，最终落到 family.name。 */
const NAME_FALLBACK: Record<Lang, string[]> = {
  en: ['en'],
  // 中文界面退到日文名而不是拉丁名：東雲ゴシック 这类汉字名，中文读者认得
  zh: ['zh-Hans', 'ja'],
  'zh-Hant': ['zh-Hant', 'zh-Hans', 'ja'],
  ja: ['ja', 'en'],
  ko: ['ko', 'en'],
  fr: ['fr', 'en'],
};

/**
 * 按界面语言取字体名。
 *
 * names 里只有作者确实起过名字的语言；缺 zh-Hant 时由简体经 OpenCC 转出，
 * 和站内其它中文一个待遇。全都没有就用 fallback（family.name，通常是拉丁名）。
 */
export function pickName(
  lang: string,
  names: Record<string, string>,
  fallback: string,
): string {
  for (const key of NAME_FALLBACK[lang as Lang] ?? ['en']) {
    const v = names[key];
    if (!v) continue;
    // 繁体缺省时从简体转，但日文名不能转——那是日语，不是中文
    return lang === 'zh-Hant' && key === 'zh-Hans' ? toHant(v) : v;
  }
  return fallback;
}

/**
 * 取一段随语言而变的文本。
 *
 * 字体元数据只有中英两份：繁体由简体转换得来，其余语言回落英文——这是
 * 收录之初就定下的规则，新增语言不必回头补 130 个家族的简介。
 */
export function pickText(lang: string, zhText: string, enText: string): string {
  if (lang === 'zh') return zhText || enText;
  if (lang === 'zh-Hant') return zhText ? toHant(zhText) : enText;
  return enText || zhText;
}

/**
 * 「主要备选语言」：中文系去英文，其余去简体中文。
 *
 * 六种语言用菜单呈现，没有唯一的「另一种语言」了；这个函数只用来在菜单里
 * 标出那个最可能被点的选项（也是端到端测试的落点）。
 */
export function otherLang(lang: string): Lang {
  return lang === 'zh' || lang === 'zh-Hant' ? 'en' : 'zh';
}

export { toHant };
export type { Lang, UIStrings };
