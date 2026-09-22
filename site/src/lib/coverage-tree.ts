/** Display hierarchy within each coverage section, independent of filter/index order. */
const children: Record<string, string[]> = {
  gb2312: ['gb2312-l1', 'gb2312-l2'],
  'gb18030-2022-l3': ['gb18030-2022-l2'],
  'gb18030-2022-l2': ['gb18030-2022-l1'],
  'tongyong-guifan': ['tongyong-guifan-l1', 'tongyong-guifan-l2', 'tongyong-guifan-l3'],
  'changyong-3500': ['changyong-2500', 'cichangyong-1000'],
  big5: ['big5-changyong', 'big5-cichangyong'],
  tw: ['tw-changyong-4808', 'tw-cichangyong-6343'],
  joyo: ['kyoiku'],
  kana: ['hiragana', 'katakana', 'kana-marks', 'kana-ext', 'halfwidth-kana'],
  'hangul-syllables': ['ksx1001-hangul'],
  'ksx1001-hanja': ['kr', 'kr-compat'],
  jamo: ['hangul-compat-jamo', 'hangul-jamo', 'jamo-ext'],
};

/** Map totals and subdivisions that supplement the existing reference tables. */
export const CJK_COVERAGE_ROWS: Record<string, string[]> = {
  cjk: ['han', 'combined'],
  tw: ['tw'],
  jp: ['kana', 'kana-marks', 'kana-ext'],
  kr: ['kr', 'kr-compat', 'jamo', 'jamo-ext'],
};

export function coverageTree<T extends { id: string }>(rows: T[]): (T & { depth: number; parent?: string })[] {
  const byId = new Map(rows.map(row => [row.id, row]));
  const parents = new Map(Object.entries(children).flatMap(([parent, ids]) =>
    byId.has(parent) ? ids.map(id => [id, parent] as const) : [],
  ));
  const result: (T & { depth: number; parent?: string })[] = [];
  const seen = new Set<string>();
  function append(id: string, depth: number, parent?: string) {
    const row = byId.get(id);
    if (!row || seen.has(id)) return;
    seen.add(id);
    result.push({ ...row, depth, parent });
    for (const child of children[id] ?? []) append(child, depth + 1, id);
  }
  for (const row of rows) {
    let root = row.id;
    while (parents.has(root)) root = parents.get(root)!;
    append(root, 0);
  }
  return result;
}
