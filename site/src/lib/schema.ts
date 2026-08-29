/** 管线产物的 zod 模型（契约 C5/C6）——跨语言契约的 TS 侧权威。 */

import { z } from 'zod';

export const LicenseSchema = z.object({
  spdx: z.string().nullable(),
  name: z.string(),
  commercial: z.boolean().nullable(),
  confidence: z.enum(['auto-high', 'auto-low', 'manual', 'unknown']),
});

export const VariantSchema = z.object({
  id: z.string(),
  file: z.string(),
  size: z.number().int(),
  weight: z.string(),
  spacing: z.string(),
  script: z.string().nullable(),
  glyphs: z.number().int(),
});

export const FamilyIndexSchema = z.object({
  slug: z.string(),
  name: z.string(),
  nameZh: z.string(),
  author: z.string(),
  form: z.string(),
  vibes: z.array(z.string()),
  scripts: z.array(z.string()),
  sizes: z.array(z.number().int()),
  weights: z.array(z.string()),
  spacing: z.array(z.string()),
  license: LicenseSchema,
  converted: z.boolean(),
  curated: z.boolean(),
  glyphCount: z.number().int(),
  hanInk: z.record(z.string(), z.array(z.number().int()).length(2)).nullable(),
  inkHeight: z.number().int(),
  badges: z.array(z.string()),
  coverageSummary: z.record(z.string(), z.number()),
  variants: z.array(VariantSchema).min(1),
  preview: z.string(),
  sampleLang: z.string(),
  added: z.string(),
  searchText: z.string(),
});

export const IndexSchema = z.object({
  generatedAt: z.string(),
  families: z.array(FamilyIndexSchema),
});

const Pair = z.array(z.number().int()).length(2);

export const DetailSchema = z.object({
  slug: z.string(),
  meta: FamilyIndexSchema,
  homepage: z.string(),
  repository: z.string(),
  description: z.string(),
  provenance: z.string(),
  convertedFrom: z.string(),
  licenseText: z.string().nullable(),
  licenseNote: z.string(),
  warnings: z.array(z.string()),
  metrics: z.record(z.string(), z.object({
    pixelSize: z.number().int(),
    ascent: z.number().int(),
    descent: z.number().int(),
    bbox: z.array(z.number().int()).length(4),
    hanInk: Pair.nullable(),
    capHeight: z.number().int().nullable(),
    xHeight: z.number().int().nullable(),
    maxInk: Pair,
    maxInkCps: Pair,
    monospaced: z.boolean(),
    dwidthHistogram: z.record(z.string(), z.number().int()),
  })),
  coverage: z.record(z.string(), z.record(z.string(), Pair)),
  overview: z.record(z.string(), z.object({
    total: Pair,
    planes: z.array(z.tuple([z.string(), z.number().int(), z.number().int()])),
    pua: z.array(z.tuple([z.string(), z.number().int(), z.number().int()])),
    hanTotal: Pair,
    compat: Pair,
    compatUnifiedNote: Pair,
  })),
  unicodeBlocks: z.record(
    z.string(),
    z.array(z.tuple([z.string(), z.number().int(), z.number().int()])),
  ),
  missingChars: z.record(z.string(), z.record(z.string(), z.string())),
  downloads: z.array(z.object({
    family: z.string(),
    variantId: z.string().nullable(),
    kind: z.enum(['bdf', 'pcf', 'zip', 'ttf']),
    file: z.string(),
    bytes: z.number().int(),
    sha256: z.string(),
  })),
});

export type FamilyIndex = z.infer<typeof FamilyIndexSchema>;
export type FontIndex = z.infer<typeof IndexSchema>;
export type FontDetail = z.infer<typeof DetailSchema>;
