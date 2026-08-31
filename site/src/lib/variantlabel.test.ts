import { describe, expect, test } from 'vitest';
import { variantLabels, type LabelledVariant } from './variantlabel';

const S = {
  weightNames: { regular: '常规', bold: '粗体' } as Record<string, string>,
  spacingNames: { monospaced: '等宽', proportional: '比例' } as Record<string, string>,
  widthNames: { normal: '常规', condensed: '紧缩', semicondensed: '半紧缩' } as Record<string, string>,
};

function v(over: Partial<LabelledVariant>): LabelledVariant {
  return {
    id: 'v', size: 16, weight: 'regular', spacing: 'proportional',
    width: 'normal', script: null, ...over,
  };
}

describe('variantLabels', () => {
  test('单变体只报尺寸与基本维度', () => {
    expect(variantLabels([v({})], S)).toEqual(['16px · 常规 · 比例']);
  });

  test('字宽不同的变体必须能区分', () => {
    // Galmuri11 与 Galmuri11-Condensed 同为 16px 常规比例，只差字宽
    const out = variantLabels(
      [v({ id: 'Galmuri11' }), v({ id: 'Galmuri11-Condensed', width: 'condensed' })],
      S,
    );
    expect(new Set(out).size).toBe(2);
    expect(out[1]).toContain('紧缩');
  });

  test('字宽相同时不加冗余的「常规」字宽', () => {
    const out = variantLabels([v({ id: 'a' }), v({ id: 'b', size: 12 })], S);
    expect(out.every((l) => !l.includes('· 常规 · 比例 · 常规'))).toBe(true);
  });

  test('所有维度都相同时退回变体名，绝不留下无法区分的重名', () => {
    // misc-fixed 有 6 个变体同为 13px 常规等宽，只有文件名不同
    const out = variantLabels(
      [v({ id: '6x13' }), v({ id: '6x13B' }), v({ id: '6x13O' })],
      S,
    );
    expect(new Set(out).size).toBe(3);
    expect(out[0]).toContain('6x13');
  });

  test('语言子集参与区分', () => {
    const out = variantLabels(
      [v({ id: 'a', script: 'zh-Hans' }), v({ id: 'b', script: 'ja' })],
      S,
    );
    expect(new Set(out).size).toBe(2);
  });

  test('全馆藏最坏情形：任何家族内标签都唯一', () => {
    const many = ['a', 'b', 'c', 'd'].map((id) => v({ id }));
    expect(new Set(variantLabels(many, S)).size).toBe(4);
  });

  test('兜底只补 id 中有区分度的部分，不重复公共前缀', () => {
    // ark-pixel 的港标/传承/台标三个变体，只有结尾的 hk/tr/tw 不同；
    // 整串文件名缀上去又长又读不出重点
    const out = variantLabels(
      [
        v({ id: 'ark-pixel-10px-monospaced-zh_hk', script: 'zh-Hant' }),
        v({ id: 'ark-pixel-10px-monospaced-zh_tr', script: 'zh-Hant' }),
        v({ id: 'ark-pixel-10px-monospaced-zh_tw', script: 'zh-Hant' }),
      ],
      S,
    );
    expect(new Set(out).size).toBe(3);
    expect(out.some((l) => l.endsWith('hk'))).toBe(true);
    expect(out.every((l) => !l.includes('ark-pixel-10px'))).toBe(true);
  });
});
