export const PAGE_SIZE = 24;

export function pageCount(total: number): number { return Math.max(1, Math.ceil(total / PAGE_SIZE)); }
export function pagePath(base: string, page: number): string {
  return page <= 1 ? base : `${base}page/${page}/`;
}
export function pageItems(current: number, total: number): (number | 'gap')[] {
  const pages = new Set([1, total]);
  for (let p = Math.max(1, current - 1); p <= Math.min(total, current + 1); p++) pages.add(p);
  const out: (number | 'gap')[] = [];
  let previous = 0;
  for (const p of [...pages].sort((a, b) => a - b)) {
    if (p - previous === 2) out.push(previous + 1);
    else if (p - previous > 2) out.push('gap');
    out.push(p);
    previous = p;
  }
  return out;
}

/** Build-time translations passed to catalogue islands, without conversion dictionaries. */
export interface CatalogueLabels {
  names: Record<string, string>;
  licenses: Record<string, string>;
  charsets: Record<string, string>;
}
