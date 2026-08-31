import { expect, test } from '@playwright/test';

test('about page explains metrics and lists data sources', async ({ page }) => {
  await page.goto('zh/about/');
  await expect(page.locator('main')).toContainText('墨迹');
  await expect(page.locator('main')).toContainText('宣称大小');
  await expect(page.locator('main')).toContainText('family.toml');
  const rows = page.locator('[data-testid="datasources"] tbody tr');
  await expect(rows).toHaveCount(64); // matches the number of charsets
});

test('about page english version', async ({ page }) => {
  await page.goto('en/about/');
  await expect(page.locator('main')).toContainText('ink');
  await expect(page.locator('[data-testid="datasources"] tbody tr')).toHaveCount(64);
});

test('detail page carries og image', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  await expect(page.locator('meta[property="og:image"]')).toHaveAttribute(
    'content',
    /data\/og\/wqy-bitmap-song\.png$/,
  );
});

test('404 page has pixel art and back links', async ({ page }) => {
  const res = await page.goto('this-page-does-not-exist/');
  expect(res!.status()).toBe(404);
  await expect(page.locator('[data-testid="pixel-404"]')).toBeVisible();
  await expect(page.locator('main')).toContainText('回到馆藏');
});
