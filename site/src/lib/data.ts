/** 构建期数据加载(node fs + zod 校验)与 base 路径工具。 */

import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { DetailSchema, IndexSchema, type FontDetail, type FontIndex } from './schema';

const DATA_DIR = new URL('../../public/data/', import.meta.url).pathname;

export function loadIndex(): FontIndex {
  const raw = readFileSync(join(DATA_DIR, 'index.json'), 'utf-8');
  return IndexSchema.parse(JSON.parse(raw));
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

/** 客户端/服务端通用:拼接 base 路径。 */
export function withBase(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

/** 下载物基址:生产由 CI 注入 Releases 地址,本地退回 /downloads。 */
export function downloadsBase(): string {
  return (import.meta.env.PFC_DOWNLOADS_BASE as string | undefined) ?? withBase('/downloads');
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
