/** 变体选择器的标签：同一家族内必须两两可区分。 */

export interface LabelledVariant {
  id: string;
  size: number;
  weight: string;
  spacing: string;
  width: string;
  script: string | null;
}

interface Names {
  weightNames: Record<string, string>;
  spacingNames: Record<string, string>;
  widthNames: Record<string, string>;
}

/**
 * 给一组变体生成标签。
 *
 * 只报「组内真正有差异」的维度：全是等宽就不必每条都写「等宽」，字宽全是
 * 常规就不写字宽。这样标签既短又都能互相区分。
 *
 * 维度全撞上时（misc-fixed 有 6 个变体同为 13px 常规等宽，只有文件名不同）
 * 补上变体自身的 id 兜底——宁可标签长，也不能给用户两个选不开的同名项。
 */
export function variantLabels(vs: LabelledVariant[], s: Names): string[] {
  const varies = <T>(pick: (v: LabelledVariant) => T) =>
    new Set(vs.map(pick)).size > 1;

  const showWeight = varies((v) => v.weight);
  const showSpacing = varies((v) => v.spacing);
  const showWidth = varies((v) => v.width);
  const showScript = varies((v) => v.script);

  const base = vs.map((v) => {
    const bits: string[] = [`${v.size}px`];
    // 只有一个变体时没有可比对象，仍给出字重与排布，信息量不至于太少
    if (showWeight || vs.length === 1) bits.push(s.weightNames[v.weight] ?? v.weight);
    if (showSpacing || vs.length === 1) bits.push(s.spacingNames[v.spacing] ?? v.spacing);
    if (showWidth) bits.push(s.widthNames[v.width] ?? v.width);
    if (showScript && v.script) bits.push(v.script);
    return bits.join(' · ');
  });

  // 仍有重名的，把 id 缀上；只补重名的那些，不牵连其它标签
  const count = new Map<string, number>();
  for (const b of base) count.set(b, (count.get(b) ?? 0) + 1);
  return base.map((b, i) =>
    count.get(b)! > 1 ? `${b} · ${distinguishing(vs[i]!.id, vs)}` : b,
  );
}

/**
 * 从变体 id 里取出有区分度的尾部。
 *
 * 同一家族的 id 往往共享长前缀（ark-pixel-10px-monospaced-zh_hk / …_zh_tw），
 * 整串缀进标签又长又读不出重点，剥掉公共前缀后只剩 hk / tw 这样的关键差异。
 */
function distinguishing(id: string, all: LabelledVariant[]): string {
  // 只跟「同样重名」的那几个比：跨尺寸的变体会让公共前缀提前分叉，
  // 结果把 10px-monospaced-zh_hk 整串留下来
  const peers = all.filter((v) => v.id !== id);
  if (!peers.length) return id;
  const parts = id.split(/[-_]/);
  // 从尾部起逐段加长，取第一个能与所有同侪区分开的后缀
  for (let n = 1; n <= parts.length; n += 1) {
    const tail = parts.slice(parts.length - n).join('-');
    const unique = peers.every((v) => !v.id.endsWith(tail));
    if (unique) return tail;
  }
  return id;
}
