import { expect, test } from '@playwright/test';

test('coverage report shows charset rows with denominators', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const report = page.getByTestId('coverage-report');
  const gbRow = report.locator('[data-charset="gb2312"]').first();
  await expect(gbRow).toContainText('GB/T 2312');
  await expect(gbRow).toContainText('6,763');
  await expect(report.first()).toContainText('已编码字符');
});

test('missing chars expandable for small sets', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const row = page.locator('[data-variant-panel]:not([hidden]) [data-charset="hiragana"]');
  await row.locator('summary').click();
  const chars = row.locator('.cov__missing-chars');
  await expect(chars).toBeVisible();
  await expect(chars).toContainText('ぁ');
});

test('coverage switches with variant', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const panels = page.getByTestId('coverage-report').locator('[data-variant-panel]');
  await expect(panels.first()).toBeVisible();
  await expect(panels.nth(1)).toBeHidden();
  await page.getByTestId('variant-select').selectOption({ index: 1 });
  await expect(panels.nth(1)).toBeVisible();
});

test('glyph grid renders sheets and inspector', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const sheet = grid.locator('.gg__sheet canvas').first();
  await expect(sheet).toBeVisible();
  await expect
    .poll(() => sheet.evaluate((c: HTMLCanvasElement) => c.dataset['cell'] ?? ''))
    .not.toBe('');
  // U+0000 块:A(U+41)位于 row 4 col 1
  const cell = await sheet.evaluate((c: HTMLCanvasElement) => Number(c.dataset['cell']));
  const rect = await sheet.boundingBox();
  const scale = rect!.width / (16 * cell);
  await sheet.click({
    position: { x: (1 * cell + cell / 2) * scale, y: (4 * cell + cell / 2) * scale },
  });
  const inspector = page.getByTestId('glyph-inspector');
  await expect(inspector).toBeVisible();
  await expect(inspector).toContainText('U+0041');
  await expect(inspector).toContainText('8px');
});

test('char lookup filters catalogue', async ({ page }) => {
  await page.goto('zh/');
  await page.getByTestId('chars-input').fill('永');
  await expect(page.getByTestId('result-count')).toHaveText('2 款字体');
  await page.getByTestId('chars-input').fill('丕');
  await expect(page.getByTestId('result-count')).toHaveText('0 款字体');
  await expect(page.getByTestId('catalogue-island')).toContainText('没有符合条件的字体');
});
