/** Build-time data loading (node fs + zod validation) and base-path utilities. */

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
  // When the data contract changes but old data is still on disk, give an
  // actionable message up front — handing this straight to zod would leave
  // the developer staring at an unreadable validation stack trace
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

/** Shared between client and server: join the base path. */
export function withBase(path: string): string {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}${path.startsWith('/') ? path : `/${path}`}`;
}

/** Base URL for downloads: CI injects the Releases URL in production, falls back to /downloads locally. */
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
