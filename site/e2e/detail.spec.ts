import { expect, test } from '@playwright/test';

test('detail page shows metadata and license', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  await expect(page.locator('h1')).toContainText('文泉驿点阵宋体');
  await expect(page.getByTestId('meta-author')).toContainText('WenQuanYi');
  await expect(page.getByTestId('license-box')).toContainText('GPL');
  await expect(page.getByTestId('license-box')).toContainText('自动识别');
  await page.getByTestId('license-details').locator('summary').click();
  await expect(page.getByTestId('license-details')).toContainText(
    'GNU GENERAL PUBLIC LICENSE',
  );
});

test('downloads list has per-variant files with sizes', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const dl = page.getByTestId('download-list');
  await expect(dl.locator('a[data-kind="bdf"]').first()).toHaveAttribute(
    'href',
    /wqy-bitmap-song--.*\.bdf\.gz$/,
  );
  await expect(dl.locator('a[data-kind="pcf"]').first()).toHaveAttribute(
    'href',
    /\.pcf\.gz$/,
  );
  await expect(dl.locator('[data-kind="zip"]')).toHaveAttribute(
    'href',
    /wqy-bitmap-song\.zip$/,
  );
  await expect(dl).toContainText('MB');
});

test('sample editor renders, missing highlight counts', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const editor = page.getByTestId('sample-editor');
  const canvas = editor.locator('canvas');
  await expect(canvas).toBeVisible();
  // ௵(泰米尔文数字符号)不在 wqy 里 → 缺 1 字
  await editor.locator('textarea').fill('永A௵');
  await expect(editor.getByTestId('missing-count')).toContainText('1');
});

test('variant switcher toggles metrics panels', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const first = page.locator('[data-variant-panel]').first();
  const second = page.locator('[data-variant-panel]').nth(1);
  await expect(first).toBeVisible();
  await expect(second).toBeHidden();
  await page.getByTestId('variant-select').selectOption({ index: 1 });
  await expect(second).toBeVisible();
  await expect(first).toBeHidden();
});

test('ink diagram present with claimed and ink boxes', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const diagram = page.getByTestId('ink-diagram');
  await expect(diagram.locator('[data-box="claimed"]').first()).toBeVisible();
  await expect(diagram.locator('[data-box="han"]').first()).toBeVisible();
  await expect(page.getByTestId('metrics-table').first()).toContainText('12×12');
});

test('en detail page renders', async ({ page }) => {
  await page.goto('en/fonts/wqy-bitmap-song/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByTestId('license-box')).toContainText('Auto-detected');
});
