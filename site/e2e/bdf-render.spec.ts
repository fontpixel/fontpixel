import { expect, test } from '@playwright/test';

test('default cards use SVG; editable text reuses one downloadable BDF', async ({ page }) => {
  const requests: string[] = [];
  page.on('request', (r) => { if (/\.bdf\.gz|\/packs\//.test(r.url())) requests.push(r.url()); });
  await page.goto('en/?q=fusion-pixel');
  const card = page.locator('[data-testid="catalogue-island"] [data-slug="fusion-pixel"]');
  await expect(card.locator('.card__sample svg')).toBeVisible();
  expect(requests).toEqual([]);
  await page.getByTestId('sample-input').fill('天地玄黃 ABC');
  await expect.poll(async () => Number(await card.locator('.card__sample canvas').getAttribute('width'))).toBeGreaterThan(0);
  const bdfs = requests.filter((url) => url.includes('fusion-pixel--fusion-pixel-12px-proportional-zh_hant.bdf.gz'));
  expect(bdfs).toHaveLength(1);
  await page.getByTestId('sample-input').fill('宇宙洪荒 XYZ');
  await expect(card.locator('.card__sample canvas')).toBeVisible();
  await page.getByTestId('sample-input').fill('');
  await expect(card.locator('.card__sample svg')).toBeVisible();
  expect(requests.some((url) => url.includes('/packs/'))).toBe(false);
  expect(requests.filter((url) => url.includes('fusion-pixel--fusion-pixel-12px-proportional-zh_hant.bdf.gz'))).toHaveLength(1);
});

test('editor and glyph browser share the BDF and preserve CJK variants', async ({ page }) => {
  const requests: string[] = [];
  const failures: string[] = [];
  page.on('request', (r) => { if (/\.bdf\.gz|\/packs\//.test(r.url())) requests.push(r.url()); });
  page.on('pageerror', (error) => failures.push(error.message));
  await page.goto('en/fonts/fusion-pixel/');
  const editor = page.getByTestId('sample-editor');
  await expect.poll(async () => Number(await editor.locator('canvas').first().getAttribute('width'))).toBeGreaterThan(0);
  await editor.locator('textarea').fill('落霞與孤鶩齊飛');
  await expect(editor.getByTestId('missing-count')).toHaveCount(0);
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  await expect(grid.getByTestId('range-select')).toBeVisible();
  await grid.getByTestId('range-select').selectOption({ label: 'CJK Unified Ideographs (U+4E00–U+9FFF)' });
  await expect.poll(async () => Number(await grid.locator('.gg__sheet canvas').first().getAttribute('width'))).toBeGreaterThan(0);
  await grid.locator('.gg__sheet canvas').first().click({ position: { x: 5, y: 5 } });
  await expect(grid.getByTestId('glyph-inspector')).toContainText('U+4E00');
  await page.getByTestId('variant-select').selectOption('fusion-pixel-12px-proportional-ja');
  await editor.locator('textarea').fill('色は匂へど');
  await expect(editor.getByTestId('missing-count')).toHaveCount(0);
  await expect.poll(() => requests.filter((url) => url.endsWith('fusion-pixel--fusion-pixel-12px-proportional-ja.bdf.gz')).length).toBe(1);
  expect(requests.filter((url) => url.endsWith('fusion-pixel--fusion-pixel-12px-proportional-zh_hant.bdf.gz'))).toHaveLength(1);
  expect(requests.some((url) => url.includes('/packs/'))).toBe(false);
  expect(failures).toEqual([]);
});
