import { describe, expect, it } from 'vitest';
import { CODE_LANGS, highlightCode } from './codehl';

const HEX = (c: readonly number[] | null | undefined) =>
  c ? c.slice(0, 3).map((n) => n.toString(16).padStart(2, '0')).join('') : null;

describe('highlightCode', () => {
  it('输出长度与码位序对齐（含换行与非 BMP 字符）', () => {
    const code = 'const a = 1;\n// 😀 emoji\nlet b = "x";';
    const out = highlightCode(code, 'javascript');
    expect(out.length).toBe(Array.from(code).length);
  });

  it('注释、字符串、数字、关键字各归各色', () => {
    const code = '// hi\nconst n = 42 + fn("s");';
    const out = highlightCode(code, 'javascript');
    const chars = Array.from(code);
    const src = chars.join('');
    expect(HEX(out[0])).toBe('6a9955'); // comment
    expect(HEX(out[src.indexOf('const')])).toBe('569cd6'); // keyword
    expect(HEX(out[src.indexOf('42')])).toBe('b5cea8'); // number
    expect(HEX(out[src.indexOf('"') + 1])).toBe('ce9178'); // string content
    expect(HEX(out[src.indexOf('fn(')])).toBe('dcdcaa'); // call name
    expect(out[src.indexOf('n =')]).toBeNull(); // plain identifiers use the default ink color
  });

  it('Python 井号注释与三引号字符串', () => {
    const code = '# c\ns = """a\nb"""\nx = 1';
    const out = highlightCode(code, 'python');
    const chars = Array.from(code);
    expect(HEX(out[0])).toBe('6a9955');
    expect(HEX(out[chars.indexOf('a')])).toBe('ce9178');
    expect(HEX(out[chars.indexOf('b')])).toBe('ce9178'); // still inside the string across lines
    expect(HEX(out[chars.lastIndexOf('1')])).toBe('b5cea8');
  });

  it('Rust 生命周期不吞行', () => {
    const code = "fn f<'a>(x: &'a str) -> u32 { 7 }";
    const out = highlightCode(code, 'rust');
    const chars = Array.from(code);
    expect(HEX(out[chars.indexOf('7')])).toBe('b5cea8'); // not mistaken for a string
  });

  it('每种语言都能跑完典型片段', () => {
    for (const lang of CODE_LANGS) {
      const out = highlightCode('x = f(1) // "s"\n', lang);
      expect(out.length).toBe(16);
    }
  });
});
