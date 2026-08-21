import { expect, test, type Page } from '@playwright/test';

const ISLAND = '[data-testid="catalogue-island"]';

async function resultCount(page: Page): Promise<number> {
  const text = await page.getByTestId('result-count').textContent();
  return Number.parseInt(text!.match(/\d+/)![0], 10);
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
  await page.getByTestId('search-input').fill('galmuri');
  await expect.poll(() => resultCount(page)).toBe(1);
  await expect(page.locator(`${ISLAND} .card[data-slug="galmuri"]`)).toBeVisible();
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

test('coverage preset filters by badge charset', async ({ page }) => {
  await page.goto('zh/');
  const all = await resultCount(page);
  // GB/T 2312 ≥99%:unifont-ex 与 wqy 达标,方舟(3583/3755)不达标
  await page
    .locator('[data-testid="filter-panel"] .chipbtn', { hasText: 'GB/T 2312' })
    .click();
  await expect.poll(() => resultCount(page)).toBeLessThan(all);
  await expect(
    page.locator(`${ISLAND} .card[data-slug="wqy-bitmap-song"]`),
  ).toBeVisible();
});
