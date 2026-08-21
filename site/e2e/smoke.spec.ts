import { expect, test } from '@playwright/test';

test('zh catalogue renders with brand and cards', async ({ page }) => {
  await page.goto('zh/');
  await expect(page).toHaveTitle(/点阵字库/);
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hans');
  await expect(page.locator('.site-brand__name')).toHaveText('点阵字库');
  const island = page.locator('[data-testid="catalogue-island"]');
  expect(await island.locator('.card').count()).toBeGreaterThanOrEqual(5);
  await expect(
    page.locator('link[rel="alternate"][hreflang="en"]').first(),
  ).toHaveAttribute('href', /\/en\//);
});

test('en page has english lang attribute and switch back', async ({ page }) => {
  await page.goto('en/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  const sw = page.getByTestId('lang-switch');
  await expect(sw).toHaveAttribute('href', /\/zh\//);
});

test('theme toggle persists', async ({ page }) => {
  await page.goto('zh/');
  const html = page.locator('html');
  const initial = await html.getAttribute('data-theme');
  await page.getByTestId('theme-toggle').click();
  const flipped = await html.getAttribute('data-theme');
  expect(flipped).not.toBe(initial);
  expect(await page.evaluate(() => localStorage.getItem('pfc-theme'))).toBe(flipped);
  await page.reload();
  await expect(html).toHaveAttribute('data-theme', flipped!);
});

test('root redirects by browser language', async ({ page }) => {
  await page.goto('.');
  await page.waitForURL(/\/(zh|en)\//);
});

test('island card renders sample canvas', async ({ page }) => {
  await page.goto('zh/');
  await expect(
    page.locator('[data-testid="catalogue-island"] .card__sample canvas').first(),
  ).toBeVisible();
});
