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
  await page.locator('[data-testid="filter-panel"] [data-form="song"]').click();
  await expect.poll(() => resultCount(page)).toBeLessThan(all);
  await expect(page).toHaveURL(/forms=song/);
  const cards = page.locator(`${ISLAND} .card`);
  expect(await cards.count()).toBeGreaterThan(0);
  for (const meta of await cards.locator('.card__meta').all()) await expect(meta).toContainText('宋体 / 明朝体');
});

test('url state restores filters on load', async ({ page }) => {
  await page.goto('zh/?forms=song');
  await expect(page.locator('[data-testid="filter-panel"] [data-form="song"]')).toHaveClass(/\bon\b/);
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
  await page.goto('zh/?q=galmuri');
  await expect(page.locator(`${ISLAND} [data-slug="galmuri"] .card__sample svg`)).toBeVisible();
  await page.getByTestId('sample-input').fill('ABC');
  const before = await cardCanvasData(page, 'galmuri');
  await page.getByTestId('sample-input').fill('픽셀 폰트 1234');
  await expect.poll(() => cardCanvasData(page, 'galmuri')).not.toBe(before);
});

test('zoom changes fixed SVG height', async ({ page }) => {
  await page.goto('zh/?q=galmuri');
  const sel = `${ISLAND} .card[data-slug="galmuri"] .card__sample svg`;
  await expect(page.locator(sel)).toBeVisible();
  const h2 = Number(await page.locator(sel).getAttribute('height'));
  await page.getByTestId('zoom-select').selectOption('3');
  await expect
    .poll(async () => Number(await page.locator(sel).getAttribute('height')))
    .toBeGreaterThan(h2);
});

test('reset clears filters including the name search, and preserves sorting', async ({ page }) => {
  await page.goto('zh/?forms=song&q=wenquanyi&sort=name');
  await expect(page.locator('[data-testid="filter-panel"] [data-form="song"]')).toHaveClass(/\bon\b/);
  await expect(page.getByTestId('search-input')).toHaveValue('wenquanyi');
  await expect(page.locator('.cat__filters').getByTestId('search-input')).toHaveCount(0);
  const filtered = await resultCount(page);
  await page.locator('[data-testid="filter-panel"] .fp__reset').click();
  await expect(page.getByTestId('search-input')).toHaveValue('');
  await expect(page.getByTestId('sort-select')).toHaveValue('name');
  await expect(page).not.toHaveURL(/[?&](q|forms)=/);
  await expect.poll(() => resultCount(page)).toBeGreaterThan(filtered);
});

test('search stays visible when filters are collapsed on a narrow screen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('zh/');
  await expect(page.locator('.cat__filters')).not.toHaveAttribute('open', /.*/);
  await expect(page.getByTestId('filter-panel')).toBeHidden();
  await expect(page.getByTestId('search-input')).toBeVisible();
});

test('coverage form filters as you type and resets', async ({ page, request }) => {
  await page.goto('zh/');
  const all = await resultCount(page);
  const panel = page.locator('[data-testid="coverage-filter"]');
  // percentage is pre-filled to 90, selecting a charset takes effect immediately
  await expect(panel.locator('[data-testid="coverage-pct"]')).toHaveValue('90');
  await panel.locator('[data-testid="coverage-charset"]').selectOption('gb2312');
  await expect.poll(() => resultCount(page)).toBeLessThan(all);
  await panel.locator('[data-testid="coverage-pct"]').fill('99');
  await expect.poll(() => resultCount(page)).toBeLessThanOrEqual(all);
  const index = await (await request.get('/data/index.json')).json();
  const visible = await page.locator(`${ISLAND} .card`).evaluateAll(cards => cards.map(c => c.getAttribute('data-slug')));
  expect(visible.length).toBeGreaterThan(0);
  const coverageIndex = index.charsetIds.indexOf('gb2312');
  for (const slug of visible) {
    expect(index.families.find((f: { slug: string }) => f.slug === slug).coverage[coverageIndex]).toBeGreaterThanOrEqual(0.99);
  }
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
  const SLUGS = ['retro-computer', 'game-ui', 'blackletter'];
  for (const [path, expected] of [
    ['zh/', '复古电脑'],
    ['en/', 'Retro computer'],
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

  await page.getByTestId('lang-menu').locator('.navmenu__trigger').click();
  await page.getByTestId('lang-switch').click();
  await page.waitForLoadState('domcontentloaded');
  const url = new URL(page.url());
  expect(url.pathname).toBe('/en/');
  expect(url.search).toContain('cov=gb2312');
  await expect(page.getByTestId('search-input')).toHaveValue('宋');

  // the detail page has no query string, but should still switch to the same font
  await page.goto('zh/fonts/galmuri/');
  await page.getByTestId('lang-menu').locator('.navmenu__trigger').click();
  await page.getByTestId('lang-switch').click();
  await page.waitForLoadState('domcontentloaded');
  expect(new URL(page.url()).pathname).toBe('/en/fonts/galmuri/');
});

test('collapsing the filter panel on a phone does not shift the results', async ({ page }) => {
  // On a narrow screen the panel is collapsed once the island mounts. Animated like a
  // user's toggle, it grew to full height first and pushed the results down and back
  // up: a CLS of 0.86 that cost the page its Lighthouse performance score.
  await page.setViewportSize({ width: 390, height: 844 });
  await page.addInitScript(() => {
    const w = window as unknown as { __cls: number };
    w.__cls = 0;
    new PerformanceObserver((list) => {
      for (const e of list.getEntries() as unknown as { value: number; hadRecentInput: boolean }[]) {
        if (!e.hadRecentInput) w.__cls += e.value;
      }
    }).observe({ type: 'layout-shift', buffered: true });
  });
  // Lighthouse's mobile run slows the CPU 4x, so the panel is painted before the island
  // mounts; on an unthrottled machine it mounts before the first paint and nothing moves.
  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await page.goto('en/');
  await expect(page.locator(`${ISLAND} .cat__filters:not([inert])`)).toBeAttached();
  await expect(page.locator(`${ISLAND} .cat__filters`)).not.toHaveAttribute('open');
  await page.waitForTimeout(600); // past the 0.25s <details> transition
  expect(await page.evaluate(() => (window as unknown as { __cls: number }).__cls)).toBeLessThan(0.1);
});
