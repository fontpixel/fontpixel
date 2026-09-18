import type { FamilyIndex } from './schema';
import { defaultSample } from './samples';

/** Match the variant to the family's default sample, independently of the UI language. */
export function previewFor(family: FamilyIndex) {
  const selected = family.previews?.[family.sampleLang];
  return {
    sampleLang: family.sampleLang,
    ...(selected ?? {
      variantId: family.previewVariant || family.variants.reduce((a, b) => {
        const aPreferred = a.size >= 8 && a.size <= 16;
        const bPreferred = b.size >= 8 && b.size <= 16;
        return aPreferred !== bPreferred ? (bPreferred ? b : a) : b.glyphs > a.glyphs ? b : a;
      }).id,
      text: family.sampleText || defaultSample(family.sampleLang),
      file: family.preview,
    }),
  };
}
