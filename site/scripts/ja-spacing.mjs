#!/usr/bin/env node
/**
 * Remove spaces between CJK characters and Latin letters/digits in Japanese copy.
 *
 * Chinese typesetting often writes "位图 TTF" (bitmap TTF) with a space; Japanese does not: ビットマップTTF、12pxの五種類.
 * Spacing against Latin text is handled by the layout engine (アキ); a manually typed space would end up doubling the width instead.
 *
 *   node scripts/ja-spacing.mjs --check   report only, don't fix
 *   node scripts/ja-spacing.mjs           fix in place
 */
import { readFileSync, writeFileSync } from 'node:fs';

const FILES = ['src/i18n/ja.ts', 'src/content/about.ja.ts'];
const CJK = '\\u3040-\\u30ff\\u3400-\\u4dbf\\u4e00-\\u9fff\\uff00-\\uff60';
const BEFORE = new RegExp(`([${CJK}]) +([A-Za-z0-9])`, 'g');
const AFTER = new RegExp(`([A-Za-z0-9%）)]) +([${CJK}])`, 'g');

const check = process.argv.includes('--check');
let bad = 0;
for (const f of FILES) {
  let src;
  try {
    src = readFileSync(f, 'utf-8');
  } catch {
    continue;
  }
  const hits = [...src.matchAll(BEFORE), ...src.matchAll(AFTER)];
  if (!hits.length) continue;
  bad += hits.length;
  console.log(`${f}: ${hits.length} 处`);
  for (const m of hits.slice(0, 6)) console.log(`   ${JSON.stringify(m[0])} → ${JSON.stringify(m[1] + m[2])}`);
  if (!check) writeFileSync(f, src.replace(BEFORE, '$1$2').replace(AFTER, '$1$2'));
}
if (check && bad) {
  console.error(`\n共 ${bad} 处日文 CJK 与欧文之间多了空格；跑 node scripts/ja-spacing.mjs 修正`);
  process.exit(1);
}
console.log(bad ? `已修正 ${bad} 处` : '日文间距检查通过（或文件尚未生成）');
