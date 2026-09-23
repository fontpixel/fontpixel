import { expect, test } from '@playwright/test';

test('zh catalogue renders with brand and cards', async ({ page }) => {
  await page.goto('zh/');
  await expect(page).toHaveTitle('FontPixel：开源像素字体馆');
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hans');
  await expect(page.locator('.site-brand')).toContainText('FontPixel：开源像素字体馆');
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

test('catalogue alone offers a keyboard shortcut to its results region', async ({ page }) => {
  await page.goto('zh/?q=no-such-font-name');
  const skipToMain = page.getByRole('link', { name: '跳到主内容' });
  const skipToResults = page.getByTestId('skip-to-results');
  const results = page.getByTestId('catalogue-results');

  await page.keyboard.press('Tab');
  await expect(skipToMain).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(skipToResults).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(results).toBeFocused();
  await expect(page).toHaveURL(/#catalogue-results$/);

  await page.goto('zh/about/');
  await expect(page.getByTestId('skip-to-results')).toHaveCount(0);
});

test('header uses the requested icons, a tools menu, and no catalogue link', async ({ page }) => {
  await page.goto('en/');
  const nav = page.locator('.site-nav');
  await expect(nav.locator(':scope > a[href="/en/"]')).toHaveCount(0);
  for (const [path, title, icon] of [
    ['/en/compare/', 'Compare fonts', 'lucide-equal-approximately'],
    ['/en/about/', 'About', 'lucide-info'],
  ] as const) {
    const link = nav.locator(`:scope > a[href="${path}"]`);
    await expect(link).toHaveAttribute('title', title);
    await expect(link).toHaveAttribute('aria-label', title);
    await expect(link.locator('svg')).toHaveClass(new RegExp(`\\b${icon}\\b`));
    await expect(link).toHaveText('');
  }

  const tools = page.getByTestId('tools-menu');
  const toolsTrigger = tools.getByRole('link', { name: 'Tools', exact: true });
  await expect(toolsTrigger).toHaveAttribute('title', 'Tools');
  await expect(toolsTrigger).toHaveAttribute('href', '/en/tools/');
  await expect(toolsTrigger.locator('svg')).toHaveClass(/\blucide-pocket-knife\b/);
  await toolsTrigger.hover();
  await expect(tools.getByRole('menuitem')).toHaveCount(4);
  await expect(tools.getByRole('menuitem')).toHaveText([
    'bdfparser (JS/TS)',
    'bdfparser (Python)',
    'BDF Specification',
    'Font Template',
  ]);
});

test('clicking the tools icon opens the tools page', async ({ page }) => {
  await page.goto('en/');
  await page.getByTestId('tools-menu').getByRole('link', { name: 'Tools', exact: true }).click();
  await page.waitForURL(/\/en\/tools\/$/);
});

test.describe('on a touch screen', () => {
  test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 800 } });

  test('tapping the tools icon toggles its menu instead of leaving the page', async ({ page }) => {
    await page.goto('en/');
    const menu = page.getByTestId('tools-menu');
    const trigger = menu.locator('.navmenu__trigger');
    await trigger.tap();
    await expect(menu.getByRole('menuitem').first()).toBeVisible();
    expect(new URL(page.url()).pathname).toBe('/en/');
    await trigger.tap();
    await expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });
});

test('header menus stay inside the viewport', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 640 });
  await page.goto('en/');
  for (const testId of ['tools-menu', 'lang-menu']) {
    const menu = page.getByTestId(testId);
    await menu.locator('.navmenu__trigger').hover();
    await expect(menu.getByRole('menuitem').first()).toBeVisible();
    const box = await menu.locator('ul').boundingBox();
    const viewportWidth = await page.evaluate(() => document.documentElement.clientWidth);
    expect(box).not.toBeNull();
    expect(box!.x).toBeGreaterThanOrEqual(0);
    if (box!.width <= viewportWidth) {
      expect(box!.x + box!.width).toBeLessThanOrEqual(viewportWidth);
    }
    expect(box!.y).toBeGreaterThanOrEqual(0);
    expect(box!.y + box!.height).toBeLessThanOrEqual(640);
    const scroll = await menu.locator('ul').evaluate((element) => ({
      clientHeight: element.clientHeight,
      scrollHeight: element.scrollHeight,
      overflowY: getComputedStyle(element).overflowY,
    }));
    expect(scroll.scrollHeight).toBeLessThanOrEqual(scroll.clientHeight);
    expect(scroll.overflowY).toBe('visible');
  }
});

test('the language menu offers every language, each linking to the same page', async ({
  page,
}) => {
  await page.goto('zh/fonts/galmuri/');
  const menu = page.getByTestId('lang-menu');
  // The button has only an icon; the accessible name comes from aria-label/title—it labels
  // the control itself as "Language", not the current language's own name
  const trigger = menu.getByRole('button', { name: '语言' });
  await expect(trigger).toHaveAttribute('aria-label', '语言');
  await expect(trigger).toHaveAttribute('title', '语言');
  await trigger.click();
  const links = menu.locator('a');
  // six languages, the current language no longer appears in the menu
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
  // every language has an hreflang alternate link
  await expect(page.locator('link[rel="alternate"][hreflang="zh-Hant"]')).toHaveCount(1);
  await expect(page.locator('link[rel="alternate"][hreflang="fr"]')).toHaveCount(1);
});

test('traditional Chinese is converted, not left in simplified', async ({ page }) => {
  await page.goto('zh-Hant/fonts/wqy-bitmap-song/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-Hant');
  await expect(page.locator('h1')).toHaveText('文泉驛點陣宋體');
  const body = await page.locator('body').innerText();
  // these simplified glyph forms shouldn't remain
  for (const ch of ['体', '点', '阵', '许', '证']) {
    expect(body, `simplified "${ch}" should not appear`).not.toContain(ch);
  }
});

test('theme toggle persists', async ({ page }) => {
  await page.goto('zh/');
  const html = page.locator('html');
  const initial = await html.getAttribute('data-theme');
  await page.getByTestId('theme-toggle').click();
  // The theme is applied inside a view transition's update callback, a frame later.
  const flipped = initial === 'dark' ? 'light' : 'dark';
  await expect(html).toHaveAttribute('data-theme', flipped);
  await expect(html).not.toHaveClass(/theme-vt/);
  expect(await page.evaluate(() => localStorage.getItem('opf-theme'))).toBe(flipped);
  await page.reload();
  await expect(html).toHaveAttribute('data-theme', flipped);
});

test('root redirects by browser language', async ({ page }) => {
  await page.goto('.');
  await page.waitForURL(/\/(zh|en)\//);
});

test('island card renders a fixed SVG sample', async ({ page }) => {
  await page.goto('zh/');
  await expect(
    page.locator('[data-testid="catalogue-island"] .card__sample svg').first(),
  ).toBeVisible();
});

test('language menu opens on hover and closes when the pointer leaves', async ({
  page,
}) => {
  await page.goto('zh/');
  const menu = page.getByTestId('lang-menu');
  const link = page.getByTestId('lang-switch');
  await expect(link).toBeHidden();

  await menu.locator('.navmenu__trigger').hover();
  await expect(link).toBeVisible();

  // move elsewhere on the page, the menu closes (closing has a 120ms buffer, waited out via toBeHidden's retry)
  await page.locator('.site-brand').hover();
  await expect(link).toBeHidden();
});

test('language menu opens on keyboard focus and closes on Escape', async ({
  page,
}) => {
  await page.goto('zh/');
  const trigger = page.getByTestId('lang-menu').getByRole('button', { name: '语言' });
  const link = page.getByTestId('lang-switch');

  // only keyboard-originated focus expands it, so actually press Tab—programmatic focus
  // doesn't trigger :focus-visible in Chromium
  await page.locator('body').click({ position: { x: 2, y: 2 } });
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Tab');
    if (await trigger.evaluate((el) => el === document.activeElement)) break;
  }
  await expect(trigger).toBeFocused();
  await expect(link).toBeVisible();

  await page.keyboard.press('Escape');
  await expect(link).toBeHidden();
});

test('header menus use one Tab stop and arrow keys navigate their items', async ({ page }) => {
  await page.goto('en/');
  for (const [testId, label] of [
    ['tools-menu', 'Tools'],
    ['lang-menu', 'Language'],
  ] as const) {
    const menu = page.getByTestId(testId);
    const trigger = menu.locator('.navmenu__trigger');
    await expect(trigger).toHaveAccessibleName(label);
    const items = menu.getByRole('menuitem');

    await trigger.focus();
    await trigger.press('ArrowDown');
    await expect(items.first()).toBeFocused();
    await page.keyboard.press('ArrowDown');
    await expect(items.nth(1)).toBeFocused();
    await page.keyboard.press('ArrowUp');
    await expect(items.first()).toBeFocused();
    await page.keyboard.press('Escape');
    await expect(trigger).toBeFocused();
    await expect(trigger).toHaveAttribute('aria-expanded', 'false');
    await expect(menu.locator('[role="menuitem"]').first()).toHaveAttribute('tabindex', '-1');
  }
});

test('github link in the header points at the repository', async ({ page }) => {
  await page.goto('zh/');
  const gh = page.getByTestId('github-link');
  await expect(gh).toHaveAttribute('href', 'https://github.com/fontpixel/fontpixel');
  await expect(gh).toHaveAttribute('title', '源码');
});
