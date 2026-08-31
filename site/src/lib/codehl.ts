/** Lightweight syntax coloring for the trial-writing box's "highlight code" mode.
 *
 * Not using highlight.js / prism: they output HTML, while what's needed here
 * is a per-codepoint color array so render.ts can color each character on
 * the bitmap canvas. This is display-only, so it doesn't need full syntax
 * analysis — a state machine at the level of "comment / string / number /
 * keyword / call name / type name" is enough.
 *
 * The returned array's indices line up with the codepoint order of
 * `for (const ch of code)` (newlines occupy a slot too), matching the
 * convention used by RasterOpts.charColors.
 */

import type { Rgba } from './render';

export const CODE_LANGS = [
  'javascript',
  'typescript',
  'python',
  'java',
  'c',
  'cpp',
  'csharp',
  'php',
  'rust',
  'go',
] as const;
export type CodeLang = (typeof CODE_LANGS)[number];

export const CODE_LANG_LABELS: Record<CodeLang, string> = {
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  python: 'Python',
  java: 'Java',
  c: 'C',
  cpp: 'C++',
  csharp: 'C#',
  php: 'PHP',
  rust: 'Rust',
  go: 'Go',
};

export const CODE_LANG_EXT: Record<CodeLang, string> = {
  javascript: 'js',
  typescript: 'ts',
  python: 'py',
  java: 'java',
  c: 'c',
  cpp: 'cpp',
  csharp: 'cs',
  php: 'php',
  rust: 'rs',
  go: 'go',
};

/** Dark-background palette (VS Code Dark+ family); the canvas background is fixed black, independent of the site theme. */
export const CODE_PAPER: Rgba = [13, 13, 13, 255];
export const CODE_INK: Rgba = [212, 212, 212, 255];
const C_COMMENT: Rgba = [106, 153, 85, 255];
const C_STRING: Rgba = [206, 145, 120, 255];
const C_NUMBER: Rgba = [181, 206, 168, 255];
const C_KEYWORD: Rgba = [86, 156, 214, 255];
const C_FUNC: Rgba = [220, 220, 170, 255];
const C_TYPE: Rgba = [78, 201, 176, 255];
const C_VAR: Rgba = [156, 220, 254, 255];

const KW: Record<CodeLang, string> = {
  javascript:
    'const let var function return if else for while do switch case default break continue new class extends super this typeof instanceof in of import export from try catch finally throw async await yield delete void static get set null undefined true false',
  typescript:
    'const let var function return if else for while do switch case default break continue new class extends super this typeof instanceof in of import export from try catch finally throw async await yield delete void static get set null undefined true false interface type enum implements readonly public private protected namespace declare keyof infer as satisfies never unknown any string number boolean object symbol',
  python:
    'def return if elif else for while in not and or is class import from as with try except finally raise lambda global nonlocal pass break continue yield async await del assert match case None True False self',
  java: 'public private protected static final void int long short byte char boolean float double class interface enum extends implements return if else for while do switch case default break continue new this super package import try catch finally throw throws instanceof abstract synchronized volatile transient native record var null true false',
  c: 'int char long short unsigned signed float double void struct union enum typedef static extern const volatile register return if else for while do switch case default break continue goto sizeof inline restrict',
  cpp: 'int char long short unsigned signed float double bool void struct union enum typedef static extern const volatile return if else for while do switch case default break continue goto sizeof inline class namespace template typename public private protected virtual override final new delete this using auto constexpr nullptr true false try catch throw operator friend explicit mutable',
  csharp:
    'public private protected internal static void int long short byte char bool float double decimal string object class struct interface enum return if else for foreach while do switch case default break continue new this base namespace using try catch finally throw var async await readonly const null true false record sealed abstract virtual override partial get set in out ref params is as where',
  php: 'function return if else elseif for foreach while do switch case default break continue new class extends implements public private protected static echo print null true false use namespace try catch finally throw require include require_once include_once const global array isset unset empty as instanceof fn match abstract final interface trait',
  rust: 'fn let mut const static return if else for while loop match impl trait struct enum pub use mod crate self super where async await move ref dyn true false unsafe as in continue break type unsigned i8 i16 i32 i64 u8 u16 u32 u64 f32 f64 usize isize bool str',
  go: 'func var const type struct interface map chan return if else for range switch case default break continue package import go defer select fallthrough nil true false make new append len cap copy panic recover error string int int8 int16 int32 int64 uint float32 float64 bool byte rune',
};

interface LangCfg {
  line: string[];
  block: [string, string] | null;
  quotes: string[];
  triple: boolean;
  dollarVar: boolean;
}

function cfg(lang: CodeLang): LangCfg {
  switch (lang) {
    case 'python':
      return { line: ['#'], block: null, quotes: ['"', "'"], triple: true, dollarVar: false };
    case 'php':
      return { line: ['//', '#'], block: ['/*', '*/'], quotes: ['"', "'"], triple: false, dollarVar: true };
    case 'rust':
      // Don't treat a single quote as a string start, so an 'a lifetime doesn't swallow the rest of the line as a string
      return { line: ['//'], block: ['/*', '*/'], quotes: ['"'], triple: false, dollarVar: false };
    case 'javascript':
    case 'typescript':
      return { line: ['//'], block: ['/*', '*/'], quotes: ['"', "'", '`'], triple: false, dollarVar: false };
    default:
      return { line: ['//'], block: ['/*', '*/'], quotes: ['"', "'"], triple: false, dollarVar: false };
  }
}

const isIdStart = (ch: string) => /[A-Za-z_]/.test(ch);
const isId = (ch: string) => /[A-Za-z0-9_]/.test(ch);
const isDigit = (ch: string) => ch >= '0' && ch <= '9';

/** Color per codepoint; null means use the default ink color. */
export function highlightCode(code: string, lang: CodeLang): (Rgba | null)[] {
  const chars = Array.from(code);
  const out: (Rgba | null)[] = new Array<Rgba | null>(chars.length).fill(null);
  const c = cfg(lang);
  const kw = new Set(KW[lang].split(' '));
  const at = (i: number, s: string) => chars.slice(i, i + s.length).join('') === s;
  let i = 0;
  while (i < chars.length) {
    const ch = chars[i]!;
    // line comment
    const lineMark = c.line.find((m) => at(i, m));
    if (lineMark) {
      while (i < chars.length && chars[i] !== '\n') out[i++] = C_COMMENT;
      continue;
    }
    // block comment
    if (c.block && at(i, c.block[0])) {
      const [, close] = c.block;
      out[i] = C_COMMENT;
      i += 1;
      while (i < chars.length && !at(i, close)) out[i++] = C_COMMENT;
      for (let k = 0; k < close.length && i < chars.length; k++) out[i++] = C_COMMENT;
      continue;
    }
    // string (including Python triple quotes; an escape skips the next codepoint)
    if (c.quotes.includes(ch)) {
      const triple = c.triple && at(i, ch.repeat(3));
      const close = triple ? ch.repeat(3) : ch;
      for (let k = 0; k < close.length; k++) out[i++] = C_STRING;
      while (i < chars.length) {
        if (chars[i] === '\\' && i + 1 < chars.length) {
          out[i++] = C_STRING;
          out[i++] = C_STRING;
          continue;
        }
        if (at(i, close)) {
          for (let k = 0; k < close.length; k++) out[i++] = C_STRING;
          break;
        }
        if (!triple && chars[i] === '\n') break; // single-line strings don't span lines
        out[i++] = C_STRING;
      }
      continue;
    }
    // number (including 0x/0b, decimals, underscore separators)
    if (isDigit(ch) || (ch === '.' && isDigit(chars[i + 1] ?? ''))) {
      while (i < chars.length && /[0-9A-Fa-fxXoObB_.]/.test(chars[i]!)) out[i++] = C_NUMBER;
      continue;
    }
    // PHP variable
    if (c.dollarVar && ch === '$' && isIdStart(chars[i + 1] ?? '')) {
      out[i++] = C_VAR;
      while (i < chars.length && isId(chars[i]!)) out[i++] = C_VAR;
      continue;
    }
    // identifier: keyword → blue; followed by "(" → call name; capitalized → type name
    if (isIdStart(ch)) {
      const start = i;
      while (i < chars.length && isId(chars[i]!)) i += 1;
      const word = chars.slice(start, i).join('');
      let j = i;
      while (j < chars.length && (chars[j] === ' ' || chars[j] === '\t')) j += 1;
      const color = kw.has(word)
        ? C_KEYWORD
        : chars[j] === '('
          ? C_FUNC
          : /^[A-Z]/.test(word)
            ? C_TYPE
            : null;
      for (let k = start; k < i; k++) out[k] = color;
      continue;
    }
    i += 1;
  }
  return out;
}
