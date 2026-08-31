import { expect, test, type Page } from '@playwright/test';

const ISLAND = '[data-testid="catalogue-island"]';

async function resultCount(page: Page): Promise<number> {
  const text = await page.getByTestId('result-count').textContent();
  return Number.parseInt(text!.match(/\d+/)![0], 10);
}

/** The catalogue island hydrates via client:load: filling right after goto loses the input
 *  before hydration finishes. Refill each round—once hydration completes it takes effect,
 *  without relying on a fixed sleep or internal implementation details. */
async function searchFor(page: Page, q: string, expected: number): Promise<void> {
  await expect
    .poll(async () => {
      await page.getByTestId('search-input').fill(q);
      return resultCount(page);
    })
    .toBe(expected);
}

async function cardCanvasData(page: Page, slug: string): Promise<string> {
  const sel = `${ISLAND} .card[data-slug="${slug}"] .card__sample canvas`;
  await page.locator(sel).scrollIntoViewIfNeeded();
  await expect
    .poll(async () =>
      page.evaluate((s) => {
        const c = document.querySelector<HTMLCanvasElement>(s);
        return c && c.width > 0 && c.width !== 300 ? c.toDataURL() : '';
      }, sel),
    )
    .not.toBe('');
  return page.evaluate((s) => {
    const c = document.querySelector<HTMLCanvasElement>(s)!;
    return c.toDataURL();
  }, sel);
}

test('form filter narrows results and updates url', async ({ page }) => {
  await page.goto('zh/');
  const all = await resultCount(page);
  expect(all).toBeGreaterThanOrEqual(5);
  await page.locator('[data-testid="filter-panel"] [data-form="mingcho"]').click();
  await expect.poll(() => resultCount(page)).toBeLessThan(all);
  await expect(page).toHaveURL(/forms=mingcho/);
  await expect(
    page.locator(`${ISLAND} .card[data-slug="wqy-bitmap-song"]`),
  ).toBeVisible();
});

test('url state restores filters on load', async ({ page }) => {
  await page.goto('zh/?forms=mingcho');
  await page.waitForSelector(`${ISLAND} .card`);
  const filtered = await resultCount(page);
  await page.goto('zh/');
  await page.waitForSelector(`${ISLAND} .card`);
  expect(await resultCount(page)).toBeGreaterThan(filtered);
});

test('search narrows results', async ({ page }) => {
  await page.goto('zh/');
  // two matches: Galmuri itself, and Quan Pixel via its former name GalmuriExtended
  await searchFor(page, 'galmuri', 2);
  await expect(page.locator(`${ISLAND} .card[data-slug="galmuri"]`)).toBeVisible();
  await expect(page.locator(`${ISLAND} .card[data-slug="quan-pixel"]`)).toBeVisible();

  // a query that only the former name matches should leave just that one
  await searchFor(page, 'GalmuriExtended', 1);
  await expect(page.locator(`${ISLAND} .card[data-slug="quan-pixel"]`)).toBeVisible();
});

test('editing sample text repaints canvas', async ({ page }) => {
  await page.goto('zh/');
  const before = await cardCanvasData(page, 'galmuri');
  await page.getByTestId('sample-input').fill('픽셀 폰트 1234');
  await expect.poll(() => cardCanvasData(page, 'galmuri')).not.toBe(before);
});

test('zoom changes canvas height', async ({ page }) => {
  await page.goto('zh/');
  await cardCanvasData(page, 'galmuri');
  const sel = `${ISLAND} .card[data-slug="galmuri"] .card__sample canvas`;
  const h2 = await page.locator(sel).evaluate((c: HTMLCanvasElement) => c.height);
  await page.getByTestId('zoom-select').selectOption('3');
  await expect
    .poll(() => page.locator(sel).evaluate((c: HTMLCanvasElement) => c.height))
    .toBeGreaterThan(h2);
});

test('invert repaints canvas', async ({ page }) => {
  await page.goto('zh/');
  const before = await cardCanvasData(page, 'galmuri');
  await page.getByTestId('invert-toggle').check();
  await expect.poll(() => cardCanvasData(page, 'galmuri')).not.toBe(before);
});

test('reset clears filters', async ({ page }) => {
  await page.goto('zh/?forms=mingcho');
  await page.waitForSelector(`${ISLAND} .card`);
  const filtered = await resultCount(page);
  await page.locator('[data-testid="filter-panel"] .fp__reset').click();
  await expect.poll(() => resultCount(page)).toBeGreaterThan(filtered);
});

test('coverage form filters as you type and resets', async ({ page }) => {
  await page.goto('zh/');
  const all = await resultCount(page);
  const panel = page.locator('[data-testid="coverage-filter"]');
  // percentage is pre-filled to 90, selecting a charset takes effect immediately
  await expect(panel.locator('[data-testid="coverage-pct"]')).toHaveValue('90');
  await panel.locator('[data-testid="coverage-charset"]').selectOption('gb2312');
  await expect.poll(() => resultCount(page)).toBeLessThan(all);
  await panel.locator('[data-testid="coverage-pct"]').fill('99');
  await expect.poll(() => resultCount(page)).toBeLessThanOrEqual(all);
  await expect(
    page.locator(`${ISLAND} .card[data-slug="wqy-bitmap-song"]`),
  ).toBeVisible();
  // lowering the threshold should include more fonts
  const strict = await resultCount(page);
  await panel.locator('[data-testid="coverage-pct"]').fill('50');
  await expect.poll(() => resultCount(page)).toBeGreaterThan(strict);
  await panel.locator('[data-testid="coverage-clear"]').click();
  await expect.poll(() => resultCount(page)).toBe(all);
});

test('search matches across simplified and traditional forms', async ({ page }) => {
  await page.goto('zh/');
  // family name is "東雲ゴシック", searching simplified "东云" should also match
  await page.getByTestId('search-input').fill('东云');
  await expect
    .poll(() =>
      page.locator(`${ISLAND} .card[data-slug="shinonome-gothic"]`).count(),
    )
    .toBe(1);
  await page.getByTestId('search-input').fill('東雲');
  await expect
    .poll(() =>
      page.locator(`${ISLAND} .card[data-slug="shinonome-gothic"]`).count(),
    )
    .toBe(1);
});

test('commercial-only filter is gone', async ({ page }) => {
  await page.goto('zh/');
  const panel = page.locator('[data-testid="filter-panel"]');
  await expect(panel).not.toContainText('仅看可商用');
  await expect(panel.locator('input[type="checkbox"]')).toHaveCount(0);
});

test('vibe tags are localised, never raw slugs', async ({ page }) => {
  // the data stores slugs like classic / retro-game / terminal-hardcore
  const SLUGS = ['retro-game', 'terminal-hardcore', 'handwriting', 'classic'];
  for (const [path, expected] of [
    ['zh/', '复古游戏'],
    ['en/', 'Retro game'],
  ] as const) {
    await page.goto(path);
    const panel = page.locator('[data-testid="filter-panel"]');
    await expect(panel).toContainText(expected);
    const text = await panel.innerText();
    for (const slug of SLUGS) {
      expect(text, `${path} should not show the raw slug ${slug}`).not.toContain(slug);
    }
  }
  // same goes for the detail page
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const side = page.locator('aside').first();
  expect(await side.innerText()).not.toContain('classic');
});

test('switching language keeps the current page and its filter state', async ({
  page,
}) => {
  await page.goto('zh/');
  await page.getByTestId('search-input').fill('宋');
  await page.getByTestId('coverage-charset').selectOption('gb2312');
  await expect.poll(() => page.url()).toContain('cov=gb2312');

  await page.getByTestId('lang-menu').locator('summary').click();
  await page.getByTestId('lang-switch').click();
  await page.waitForLoadState('domcontentloaded');
  const url = new URL(page.url());
  expect(url.pathname).toBe('/en/');
  expect(url.search).toContain('cov=gb2312');
  await expect(page.getByTestId('search-input')).toHaveValue('宋');

  // the detail page has no query string, but should still switch to the same font
  await page.goto('zh/fonts/galmuri/');
  await page.getByTestId('lang-menu').locator('summary').click();
  await page.getByTestId('lang-switch').click();
  await page.waitForLoadState('domcontentloaded');
  expect(new URL(page.url()).pathname).toBe('/en/fonts/galmuri/');
});
