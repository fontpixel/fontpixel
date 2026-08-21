import { expect, test } from '@playwright/test';

test('detail page shows metadata and license', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  await expect(page.locator('h1')).toContainText('迷你测试');
  await expect(page.getByTestId('meta-author')).toContainText('PFC Tests');
  await expect(page.getByTestId('license-box')).toContainText('OFL-1.1');
  await expect(page.getByTestId('license-box')).toContainText('自动识别');
  await page.getByTestId('license-details').locator('summary').click();
  await expect(page.getByTestId('license-details')).toContainText(
    'SIL OPEN FONT LICENSE',
  );
});

test('downloads list has per-variant files with sizes', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const dl = page.getByTestId('download-list');
  await expect(dl.locator('a', { hasText: 'BDF' }).first()).toHaveAttribute(
    'href',
    /mini--mini\.bdf\.gz$/,
  );
  await expect(dl.locator('[data-kind="zip"]')).toHaveAttribute(
    'href',
    /mini\.zip$/,
  );
  await expect(dl).toContainText('KB');
});

test('sample editor renders, missing highlight counts', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const editor = page.getByTestId('sample-editor');
  const canvas = editor.locator('canvas');
  await expect(canvas).toBeVisible();
  await editor.locator('textarea').fill('A永あ');
  await expect(editor.getByTestId('missing-count')).toContainText('1');
});

test('variant switcher toggles metrics panels', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const first = page.locator('[data-variant-panel]').first();
  const second = page.locator('[data-variant-panel]').nth(1);
  await expect(first).toBeVisible();
  await expect(second).toBeHidden();
  await page.getByTestId('variant-select').selectOption({ index: 1 });
  await expect(second).toBeVisible();
  await expect(first).toBeHidden();
});

test('ink diagram present with claimed and ink boxes', async ({ page }) => {
  await page.goto('zh/fonts/mini/');
  const diagram = page.getByTestId('ink-diagram');
  await expect(diagram.locator('[data-box="claimed"]').first()).toBeVisible();
  await expect(page.getByTestId('metrics-table').first()).toContainText('16');
});

test('en detail page renders', async ({ page }) => {
  await page.goto('en/fonts/mini/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByTestId('license-box')).toContainText('Auto-detected');
});
