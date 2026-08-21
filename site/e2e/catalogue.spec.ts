import { expect, test, type Page } from '@playwright/test';

const ISLAND = '[data-testid="catalogue-island"]';

async function cardCanvasData(page: Page, slug: string): Promise<string> {
  const sel = `${ISLAND} .card[data-slug="${slug}"] .card__sample canvas`;
  await page.locator(sel).scrollIntoViewIfNeeded();
  await expect
    .poll(async () =>
      page.evaluate((s) => {
        const c = document.querySelector<HTMLCanvasElement>(s);
        return c && c.width > 0 ? c.toDataURL() : '';
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
  await expect(page.getByTestId('result-count')).toHaveText('2 款字体');
  await page.locator('[data-testid="filter-panel"] [data-form="gothic"]').click();
  await expect(page.getByTestId('result-count')).toHaveText('1 款字体');
  await expect(page).toHaveURL(/forms=gothic/);
  await expect(page.locator(`${ISLAND} .card[data-slug="mini"]`)).toBeVisible();
});

test('url state restores filters on load', async ({ page }) => {
  await page.goto('zh/?forms=gothic');
  await expect(page.getByTestId('result-count')).toHaveText('1 款字体');
});

test('search narrows results', async ({ page }) => {
  await page.goto('zh/');
  await page.getByTestId('search-input').fill('Nometa');
  await expect(page.getByTestId('result-count')).toHaveText('1 款字体');
});

test('editing sample text repaints canvas', async ({ page }) => {
  await page.goto('zh/');
  const before = await cardCanvasData(page, 'mini');
  await page.getByTestId('sample-input').fill('AAAA AAAA');
  await expect.poll(() => cardCanvasData(page, 'mini')).not.toBe(before);
});

test('zoom changes canvas height', async ({ page }) => {
  // 样例按容器宽换行,宽度被钳住;放大必然增加高度(行高×倍数,且换行更多)
  await page.goto('zh/');
  await cardCanvasData(page, 'mini');
  const h2 = await page
    .locator(`${ISLAND} .card[data-slug="mini"] .card__sample canvas`)
    .evaluate((c: HTMLCanvasElement) => c.height);
  await page.getByTestId('zoom-select').selectOption('3');
  await expect
    .poll(() =>
      page
        .locator(`${ISLAND} .card[data-slug="mini"] .card__sample canvas`)
        .evaluate((c: HTMLCanvasElement) => c.height),
    )
    .toBeGreaterThan(h2);
});

test('invert repaints canvas', async ({ page }) => {
  await page.goto('zh/');
  const before = await cardCanvasData(page, 'mini');
  await page.getByTestId('invert-toggle').check();
  await expect.poll(() => cardCanvasData(page, 'mini')).not.toBe(before);
});

test('reset clears filters', async ({ page }) => {
  await page.goto('zh/?forms=gothic&sizes=16');
  await expect(page.getByTestId('result-count')).toHaveText('1 款字体');
  await page.locator('[data-testid="filter-panel"] .fp__reset').click();
  await expect(page.getByTestId('result-count')).toHaveText('2 款字体');
});
