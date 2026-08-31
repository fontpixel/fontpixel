/** zod models for pipeline output (contract C5/C6) — the TS-side authority for the cross-language contract. */

import { z } from 'zod';

export const LicenseSchema = z.object({
  spdx: z.string().nullable(),
  name: z.string(),
  nameEn: z.string(),
  confidence: z.enum(['auto-high', 'auto-low', 'manual', 'unknown']),
});

export const VariantSchema = z.object({
  id: z.string(),
  file: z.string(),
  size: z.number().int(),
  weight: z.string(),
  spacing: z.string(),
  width: z.string().default('normal'),
  /** Recommended display size (px) as noted in upstream docs; 0 means upstream doesn't specify */
  displaySize: z.number().default(0),
  script: z.string().nullable(),
  glyphs: z.number().int(),
});

export const FamilyIndexSchema = z.object({
  slug: z.string(),
  name: z.string(),
  names: z.record(z.string(), z.string()),
  authors: z.array(z.string()),
  authorsEn: z.array(z.string()),
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
  /** Per-variant ink heights (deduped, ascending); the filter matches when any variant falls in the range */
  inkHeights: z.array(z.number().int()),
  badges: z.array(z.string()),
  coverageSummary: z.record(z.string(), z.number()),
  coverage: z.array(z.number()),
  variants: z.array(VariantSchema).min(1),
  preview: z.string(),
  sampleLang: z.string(),
  sampleText: z.string().default(''),
  previewVariant: z.string().default(''),
  added: z.string(),
  searchText: z.string(),
});

export const CharsetMetaSchema = z.object({
  zh: z.string(),
  en: z.string(),
  section: z.string(),
  total: z.number().int(),
});

/** Site data contract version, kept in sync with DATA_SCHEMA_VERSION in pipeline/opf/__init__.py.
 *  Bump both sides by 1 whenever index.json's shape changes; going out of sync is caught by schema.test.ts. */
export const DATA_SCHEMA_VERSION = 2;

export const IndexSchema = z.object({
  schemaVersion: z.number().int(),
  generatedAt: z.string(),
  charsetIds: z.array(z.string()),
  charsetNames: z.record(z.string(), CharsetMetaSchema),
  families: z.array(FamilyIndexSchema),
});

const Pair = z.array(z.number().int()).length(2);

export const DetailSchema = z.object({
  slug: z.string(),
  meta: FamilyIndexSchema,
  homepage: z.string(),
  repository: z.string(),
  description: z.string(),
  descriptionEn: z.string(),
  provenance: z.string(),
  provenanceEn: z.string(),
  convertedFrom: z.string(),
  licenseText: z.string().nullable(),
  licenseNote: z.string(),
  licenseNoteEn: z.string(),
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
    kind: z.enum(['bdf', 'pcf', 'zip', 'ttf', 'ttf-square', 'ttf-round']),
    file: z.string(),
    bytes: z.number().int(),
    sha256: z.string(),
  })),
});

export type FamilyIndex = z.infer<typeof FamilyIndexSchema>;
export type FontIndex = z.infer<typeof IndexSchema>;
export type FontDetail = z.infer<typeof DetailSchema>;
