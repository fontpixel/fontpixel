/** Labels for the variant picker: every pair within a family must be distinguishable. */

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
 * Generate labels for a set of variants.
 *
 * Only report dimensions that actually vary within the group: if every
 * variant is monospace, no need to spell out "monospace" on each label; if
 * every width is regular, skip the width. This keeps labels short while
 * still distinguishing them.
 *
 * When every dimension collides (misc-fixed has 6 variants that are all
 * 13px regular monospace, differing only by filename), fall back to
 * appending the variant's own id — better a long label than two identical
 * entries the user can't tell apart.
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
    // With only one variant there's nothing to compare against, but still show weight and spacing so the label isn't too sparse
    if (showWeight || vs.length === 1) bits.push(s.weightNames[v.weight] ?? v.weight);
    if (showSpacing || vs.length === 1) bits.push(s.spacingNames[v.spacing] ?? v.spacing);
    if (showWidth) bits.push(s.widthNames[v.width] ?? v.width);
    if (showScript && v.script) bits.push(v.script);
    return bits.join(' · ');
  });

  // For any labels that still collide, append the id; only touch the colliding ones, leave the rest alone
  const count = new Map<string, number>();
  for (const b of base) count.set(b, (count.get(b) ?? 0) + 1);
  return base.map((b, i) =>
    count.get(b)! > 1 ? `${b} · ${distinguishing(vs[i]!.id, vs)}` : b,
  );
}

/**
 * Extract the distinguishing tail from a variant id.
 *
 * Ids within a family often share a long prefix (ark-pixel-10px-monospaced-
 * zh_hk / …_zh_tw); appending the whole string to the label is long and
 * buries the point, so stripping the common prefix leaves just the key
 * difference, like hk / tw.
 */
function distinguishing(id: string, all: LabelledVariant[]): string {
  // Only compare against the peers that share this label — comparing across
  // sizes would make the common prefix diverge too early, leaving the whole
  // "10px-monospaced-zh_hk" string in the result
  const peers = all.filter((v) => v.id !== id);
  if (!peers.length) return id;
  const parts = id.split(/[-_]/);
  // Grow the tail one segment at a time from the end, taking the first suffix that distinguishes it from all peers
  for (let n = 1; n <= parts.length; n += 1) {
    const tail = parts.slice(parts.length - n).join('-');
    const unique = peers.every((v) => !v.id.endsWith(tail));
    if (unique) return tail;
  }
  return id;
}
