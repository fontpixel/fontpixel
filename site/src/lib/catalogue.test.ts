import { expect, test } from 'vitest';
import { PAGE_SIZE, pageCount, pageItems, pagePath } from './catalogue';

const fonts = Array.from({ length: 411 }, (_, i) => ({
  slug: `font-${i}`, glyphCount: (i + 1) * 128, scripts: i % 4 ? ['latin'] : ['ja', 'ko'],
}));

test('all 18 pages contain every family exactly once', () => {
  const order = fonts;
  const pages = Array.from({ length: pageCount(order.length) }, (_, i) => order.slice(i * PAGE_SIZE, (i + 1) * PAGE_SIZE));
  expect(pages).toHaveLength(18);
  expect(pages.at(-1)).toHaveLength(3);
  expect(pages.flat()).toEqual(order);
  expect(pageCount(0)).toBe(1);
  expect(pageCount(24)).toBe(1);
});
test('pagination keeps clean URLs and compact, ordered, unique page links', () => {
  expect(pagePath('/base/en/', 1)).toBe('/base/en/');
  expect(pagePath('/base/en/', 18)).toBe('/base/en/page/18/');
  expect(pageItems(1, 18)).toEqual([1, 2, 'gap', 18]);
  expect(pageItems(4, 18)).toEqual([1, 2, 3, 4, 5, 'gap', 18]);
  for (let current = 1; current <= 18; current++) {
    const items = pageItems(current, 18).filter(p => typeof p === 'number');
    expect(items).toContain(current);
    expect(items).toEqual([...new Set(items)].sort((a, b) => a - b));
  }
});
