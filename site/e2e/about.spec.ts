import { expect, test } from '@playwright/test';

test('about page explains metrics and lists data sources', async ({ page }) => {
  await page.goto('zh/about/');
  await expect(page.locator('main')).toContainText('墨迹');
  await expect(page.locator('main')).toContainText('宣称大小');
  await expect(page.locator('main')).toContainText('family.toml');
  const rows = page.locator('[data-testid="datasources"] tbody tr');
  await expect(rows).toHaveCount(66); // matches the number of charsets (thai added 2026-09-03)
});

test('about page english version', async ({ page }) => {
  await page.goto('en/about/');
  await expect(page.locator('main')).toContainText('ink');
  await expect(page.locator('[data-testid="datasources"] tbody tr')).toHaveCount(66);
});

test('all About translations link the author and exclusion sources on narrow screens', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  for (const lang of ['zh', 'zh-Hant', 'en', 'ja', 'ko', 'fr']) {
    await page.goto(`${lang}/about/`);
    const intro = page.locator('.about__intro');
    await expect(intro).toContainText('FontPixel.com');
    await expect(intro.getByRole('link', { name: 'Tom Chen', exact: true }))
      .toHaveAttribute('href', 'https://tomchen.org/');
    const examples = page.locator('#criteria .about__examples');
    await expect(examples.locator('li')).toHaveCount(5);
    await expect(examples.locator('li strong a')).toHaveCount(5);
    await expect(examples.locator('a[href="https://timothyqiu.itch.io/vonwaon-bitmap"]')).toHaveCount(1);
    await expect(examples.locator('a[href="https://github.com/Angelic47/FontChinese7x7/issues/6"]')).toHaveCount(1);
    await expect(examples).toContainText('lietxia');
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
  }
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
