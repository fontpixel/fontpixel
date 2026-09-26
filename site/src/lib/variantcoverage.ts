/** Per-variant coverage ratios of multi-variant families (variant-coverage.json), lazy-loaded
 *  by the catalogue only while a coverage filter is active. Single-variant families are absent:
 *  the index's family ratios already describe their one variant. */
import type { VariantCoverageLookup } from './filters';

interface VariantCoverageFile {
  charsetIds: string[];
  families: Record<string, Record<string, number[]>>;
}

let cached: Promise<VariantCoverageFile> | null = null;

/** Resolve a lookup whose arrays follow `charsetIds`, the order the index uses. */
export async function loadVariantCoverage(
  dataBase: string,
  charsetIds: readonly string[],
  fetchFn: typeof fetch = (input, init) => globalThis.fetch(input, init),
): Promise<VariantCoverageLookup> {
  if (!cached) {
    cached = (async () => {
      const res = await fetchFn(`${dataBase}/variant-coverage.json`);
      if (!res.ok) throw new Error(`variant coverage: ${res.status}`);
      return (await res.json()) as VariantCoverageFile;
    })();
    cached.catch(() => (cached = null));
  }
  const file = await cached;
  const aligned = file.charsetIds.length === charsetIds.length
    && file.charsetIds.every((id, i) => id === charsetIds[i]);
  const order = aligned ? null : charsetIds.map((id) => file.charsetIds.indexOf(id));
  return (slug, variantId) => {
    const ratios = file.families[slug]?.[variantId];
    if (!ratios || !order) return ratios;
    return order.map((i) => (i === -1 ? 0 : ratios[i] ?? 0));
  };
}
