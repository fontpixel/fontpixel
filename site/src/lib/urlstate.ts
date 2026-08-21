/** FilterState ↔ URL query 序列化（可分享链接）。未知参数忽略。 */

import { emptyState, type FilterState, type SortKey } from './filters';

const SORTS: SortKey[] = ['name', 'size', 'glyphs', 'added'];

export function encodeState(s: FilterState): URLSearchParams {
  const p = new URLSearchParams();
  const d = emptyState();
  if (s.q) p.set('q', s.q);
  if (s.forms.length) p.set('forms', s.forms.join(','));
  if (s.vibes.length) p.set('vibes', s.vibes.join(','));
  if (s.sizes.length) p.set('sizes', s.sizes.join(','));
  if (s.inkH) p.set('ink', `${s.inkH[0]}-${s.inkH[1]}`);
  if (s.scripts.length) p.set('scripts', s.scripts.join(','));
  if (s.licenses.length) p.set('lic', s.licenses.join(','));
  if (s.commercialOnly) p.set('com', '1');
  if (s.spacing.length) p.set('sp', s.spacing.join(','));
  if (s.weights.length) p.set('wt', s.weights.join(','));
  if (s.origin !== d.origin) p.set('or', s.origin);
  if (s.coverage.length)
    p.set('cov', s.coverage.map((c) => `${c.id}:${c.min}`).join(','));
  if (s.chars) p.set('chars', s.chars);
  if (s.sort !== d.sort) p.set('sort', s.sort);
  return p;
}

function list(p: URLSearchParams, key: string): string[] {
  const v = p.get(key);
  return v ? v.split(',').filter(Boolean) : [];
}

export function decodeState(p: URLSearchParams): FilterState {
  const s = emptyState();
  s.q = p.get('q') ?? '';
  s.forms = list(p, 'forms');
  s.vibes = list(p, 'vibes');
  s.sizes = list(p, 'sizes')
    .map((x) => Number.parseInt(x, 10))
    .filter((n) => Number.isFinite(n));
  const ink = p.get('ink');
  if (ink) {
    const m = ink.match(/^(\d+)-(\d+)$/);
    if (m) s.inkH = [Number.parseInt(m[1]!, 10), Number.parseInt(m[2]!, 10)];
  }
  s.scripts = list(p, 'scripts');
  s.licenses = list(p, 'lic');
  s.commercialOnly = p.get('com') === '1';
  s.spacing = list(p, 'sp');
  s.weights = list(p, 'wt');
  const or = p.get('or');
  if (or === 'native' || or === 'converted') s.origin = or;
  s.coverage = list(p, 'cov')
    .map((x) => {
      const [id, min] = x.split(':');
      return { id: id ?? '', min: Number.parseFloat(min ?? '') };
    })
    .filter((c) => c.id && Number.isFinite(c.min));
  s.chars = p.get('chars') ?? '';
  const sort = p.get('sort') as SortKey | null;
  if (sort && SORTS.includes(sort)) s.sort = sort;
  return s;
}
