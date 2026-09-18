/** Server only: static pages and the hydrated catalogue share the same fixed rating. */
import { loadIndex } from './data';
import { ratingOrder } from './rating';

export function loadCatalogue() {
  const index = loadIndex();
  return { ...index, families: ratingOrder(index.families, index.charsetIds) };
}
