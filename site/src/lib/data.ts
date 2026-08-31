/** 构建期数据加载（node fs + zod 校验）与 base 路径工具。 */

import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import {
  DATA_SCHEMA_VERSION,
  DetailSchema,
  IndexSchema,
  type FontDetail,
  type FontIndex,
} from './schema';

const DATA_DIR = new URL('../../public/data/', import.meta.url).pathname;

export function loadIndex(): FontIndex {
  let raw: string;
  try {
    raw = readFileSync(join(DATA_DIR, 'index.json'), 'utf-8');
  } catch {
    throw new Error(
      '站点数据尚未构建：public/data/index.json 不存在。请在仓库根目录运行 make fonts。\n' +
        'Site data has not been built yet (public/data/index.json is missing). Run `make fonts` at the repo root.',
    );
  }
  const parsed = JSON.parse(raw) as { schemaVersion?: number };
  // 数据契约一变、旧数据还躺在磁盘上时，先给出一句能照做的提示——
  // 直接交给 zod 的话，开发者看到的是一页读不懂的校验堆栈
  if (parsed.schemaVersion !== DATA_SCHEMA_VERSION) {
    throw new Error(
      `站点数据是旧格式（schemaVersion=${parsed.schemaVersion ?? '无'}，需要 ${DATA_SCHEMA_VERSION}）。` +
        '请在仓库根目录运行 make fonts 重建。\n' +
        `Site data is in an old format (schemaVersion=${parsed.schemaVersion ?? 'none'}, expected ${DATA_SCHEMA_VERSION}). Run \`make fonts\` at the repo root to rebuild.`,
    );
  }
  return IndexSchema.parse(parsed);
}

export function loadDetail(slug: string): FontDetail {
  const raw = readFileSync(join(DATA_DIR, 'details', `${slug}.json`), 'utf-8');
  return DetailSchema.parse(JSON.parse(raw));
}

export function listDetailSlugs(): string[] {
  return readdirSync(join(DATA_DIR, 'details'))
    .filter((f) => f.endsWith('.json'))
    .map((f) => f.replace(/\.json$/, ''));
}

export function readPreviewSvg(relPath: string): string {
  return readFileSync(join(DATA_DIR, relPath), 'utf-8');
}

/** 客户端/服务端通用：拼接 base 路径。 */
export function withBase(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

/** 下载物基址：生产由 CI 注入 Releases 地址，本地退回 /downloads。 */
export function downloadsBase(): string {
  return (import.meta.env.OPF_DOWNLOADS_BASE as string | undefined) ?? withBase('/downloads');
}

export interface CharsetMeta {
  id: string;
  section: string;
  order: number;
  nameZh: string;
  nameEn: string;
  descZh: string;
  descEn: string;
  source: string;
  total: number;
}

export function loadCharsetsMeta(): { sections: string[]; charsets: CharsetMeta[] } {
  const raw = readFileSync(join(DATA_DIR, 'charsets.json'), 'utf-8');
  return JSON.parse(raw) as { sections: string[]; charsets: CharsetMeta[] };
}

export function readLicenseText(slug: string): string | null {
  try {
    return readFileSync(join(DATA_DIR, 'licenses', `${slug}.txt`), 'utf-8');
  } catch {
    return null;
  }
}
