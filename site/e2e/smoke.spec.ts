import { expect, test } from '@playwright/test';

test('zh catalogue renders with brand and cards', async ({ page }) => {
  await page.goto('zh/');
  await expect(page).toHaveTitle(/开源像素字体馆/);
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hans');
  await expect(page.locator('.site-brand')).toContainText('开源像素字体馆');
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

test('the language menu offers every language, each linking to the same page', async ({
  page,
}) => {
  await page.goto('zh/fonts/galmuri/');
  const menu = page.getByTestId('lang-menu');
  // summary 里只有一个图标，可及名称走 aria-label/title——标的是控件本身
  // 「语言」，不是当前语言的自称
  await expect(menu.locator('summary')).toHaveAttribute('aria-label', '语言');
  await expect(menu.locator('summary')).toHaveAttribute('title', '语言');
  await menu.locator('summary').click();
  const links = menu.locator('a');
  // 六种语言，当前语言不再出现在菜单里
  await expect(links).toHaveCount(5);
  const hrefs = await links.evaluateAll((as) =>
    as.map((a) => (a as HTMLAnchorElement).getAttribute('href')),
  );
  expect(hrefs.every((h) => h!.endsWith('/fonts/galmuri/'))).toBe(true);
  expect(hrefs).toEqual(
    expect.arrayContaining([
      '/zh-Hant/fonts/galmuri/',
      '/en/fonts/galmuri/',
      '/ja/fonts/galmuri/',
      '/ko/fonts/galmuri/',
      '/fr/fonts/galmuri/',
    ]),
  );
  // 每种语言都有 hreflang 备用链接
  await expect(page.locator('link[rel="alternate"][hreflang="zh-Hant"]')).toHaveCount(1);
  await expect(page.locator('link[rel="alternate"][hreflang="fr"]')).toHaveCount(1);
});

test('traditional Chinese is converted, not left in simplified', async ({ page }) => {
  await page.goto('zh-Hant/fonts/wqy-bitmap-song/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hant');
  await expect(page.locator('h1')).toHaveText('文泉驛點陣宋體');
  const body = await page.locator('body').innerText();
  // 这些简体字形不该残留
  for (const ch of ['体', '点', '阵', '许', '证']) {
    expect(body, `不该出现简体「${ch}」`).not.toContain(ch);
  }
});

test('theme toggle persists', async ({ page }) => {
  await page.goto('zh/');
  const html = page.locator('html');
  const initial = await html.getAttribute('data-theme');
  await page.getByTestId('theme-toggle').click();
  const flipped = await html.getAttribute('data-theme');
  expect(flipped).not.toBe(initial);
  expect(await page.evaluate(() => localStorage.getItem('opf-theme'))).toBe(flipped);
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

test('language menu opens on hover and closes when the pointer leaves', async ({
  page,
}) => {
  await page.goto('zh/');
  const menu = page.getByTestId('lang-menu');
  const link = page.getByTestId('lang-switch');
  await expect(link).toBeHidden();

  await menu.locator('summary').hover();
  await expect(link).toBeVisible();

  // 移到页面别处，菜单收起（收起有 120ms 缓冲，用 toBeHidden 的重试等它）
  await page.locator('.site-brand').hover();
  await expect(link).toBeHidden();
});

test('language menu opens on keyboard focus and closes on Escape', async ({
  page,
}) => {
  await page.goto('zh/');
  const summary = page.getByTestId('lang-menu').locator('summary');
  const link = page.getByTestId('lang-switch');

  // 只有键盘来的焦点才展开，所以真的按 Tab——programmatic focus 在 Chromium
  // 里不会命中 :focus-visible
  await page.locator('body').click({ position: { x: 2, y: 2 } });
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab');
    if (await summary.evaluate((el) => el === document.activeElement)) break;
  }
  await expect(summary).toBeFocused();
  await expect(link).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(link).toBeHidden();
});

test('github link in the header points at the repository', async ({ page }) => {
  await page.goto('zh/');
  const gh = page.getByTestId('github-link');
  await expect(gh).toHaveAttribute('href', /github\.com\/.+/);
  await expect(gh).toHaveAttribute('title', '源码');
});
