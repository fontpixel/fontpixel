import type { Lang, UIStrings } from './types';
import { zh } from './zh';
import { en } from './en';

export const LANGS: Lang[] = ['zh', 'en'];

export function t(lang: string): UIStrings {
  return lang === 'en' ? en : zh;
}

export function otherLang(lang: string): Lang {
  return lang === 'en' ? 'zh' : 'en';
}

export type { Lang, UIStrings };
