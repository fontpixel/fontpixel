import { expect, test, type Page } from '@playwright/test';
import { createRater, ratingOrder } from '../src/lib/rating';

const island = '[data-testid="catalogue-island"]';
const cards = `${island} .card`;
const slugs = (page: Page) => page.locator(cards).evaluateAll(els => els.map(el => el.getAttribute('data-slug')));
const ready = (page: Page) => expect(page.locator(island)).toHaveAttribute('data-ready', 'true');
const htmlSlugs = (html: string) => [...html.matchAll(/<article\b[^>]*data-slug="([^"]+)"/g)].map(m => m[1]);

test('rating order survives hydration, paging, refresh, detail and browser back', async ({ page }) => {
  const response = await page.goto('en/');
  const staticOrder = htmlSlugs(await response!.text());
  await ready(page);
  await expect(page).toHaveURL(/\/en\/$/);
  await expect(page.getByTestId('sort-select')).toHaveValue('rating');
  await expect(page.getByTestId('page-prev')).toHaveCount(0);
  await expect(page.getByTestId('page-next').first()).toHaveAttribute('title', 'Next');
  await expect(page.getByTestId('page-next').first()).toHaveAccessibleName('Next');
  await expect(page.getByTestId('sort-select').locator('option[value="rating"]')).toHaveText('Auto');
  await expect(page.getByTestId('sort-select').locator('option[value="random"]')).toHaveCount(0);
  await expect(page.locator(cards)).toHaveCount(24);
  expect(await slugs(page)).toEqual(staticOrder);
  await page.getByTestId('page-next').first().click();
  await ready(page);
  await expect(page).toHaveURL(/\/en\/page\/2\/$/);
  await expect(page.getByTestId('page-prev').first()).toHaveAccessibleName('Previous');
  const second = await slugs(page);
  expect(second.every(slug => !staticOrder.includes(slug!))).toBe(true);
  await page.reload();
  await ready(page);
  expect(await slugs(page)).toEqual(second);
  await page.locator(`${cards} .card__link`).first().click();
  await expect(page).toHaveURL(/\/en\/fonts\//);
  await page.goBack();
  await ready(page);
  expect(await slugs(page)).toEqual(second);
  await page.getByTestId('page-prev').first().click();
  await ready(page);
  expect(await slugs(page)).toEqual(staticOrder);
});

test('all static pages cover the catalogue once, with self canonicals and locale-independent order', async ({ request }) => {
  const index = await (await request.get('/data/index.json')).json();
  const total = Math.ceil(index.families.length / 24);
  const found: string[] = [];
  for (let n = 1; n <= total; n++) {
    const path = n === 1 ? '/en/' : `/en/page/${n}/`;
    const response = await request.get(path);
    expect(response.ok()).toBe(true);
    const html = await response.text();
    const batch = htmlSlugs(html);
    expect(batch.length).toBe(n === total ? index.families.length - (n - 1) * 24 : 24);
    expect(html).toContain(`rel="canonical" href="https://fontpixel.com${path}"`);
    found.push(...batch!);
    if (n === 2) {
      const ja = await (await request.get('/ja/page/2/')).text();
      expect(htmlSlugs(ja)).toEqual(batch);
    }
  }
  expect(found).toEqual(ratingOrder(index.families, index.charsetIds).map(f => f.slug));
  const rate = createRater(index.charsetIds);
  const scores = ratingOrder(index.families, index.charsetIds).map(f => rate(f).score);
  expect(scores).toEqual([...scores].sort((a, b) => b - a));
  expect([...found].sort()).toEqual(index.families.map((f: { slug: string }) => f.slug).sort());
});

test('static pagination and specimens work without JavaScript', async ({ browser, baseURL }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, baseURL });
  const page = await context.newPage();
  await page.goto('en/page/2/');
  await expect(page.locator(cards)).toHaveCount(24);
  await expect(page.locator(`${cards} .card__sample svg`).first()).toBeVisible();
  await page.getByTestId('page-next').first().click();
  await expect(page).toHaveURL(/\/en\/page\/3\/$/);
  await expect(page.locator(cards)).toHaveCount(24);
  await context.close();
});

test('page pencils jump on Enter and preserve sorting, specimen and zoom', async ({ page }) => {
  await page.goto('en/?sort=name');
  await ready(page);
  await page.getByTestId('sample-input').fill('ABC 123');
  await page.getByTestId('zoom-select').selectOption('3');
  const top = page.getByTestId('pagination').first();
  const pencil = top.getByTestId('page-edit').first();
  await expect(top.locator('.page-edit:first-child + [data-page="1"]')).toHaveCount(1);
  await expect(pencil).toHaveAttribute('title', 'Edit page number');
  await expect(pencil.locator('svg')).toHaveClass(/lucide-pencil/);
  await pencil.click();
  await expect(top.getByTestId('page-input')).toBeFocused();
  await expect(top.getByTestId('page-input')).toHaveValue('1');
  await top.getByTestId('page-input').fill('7');
  await top.getByTestId('page-input').press('Enter');
  await ready(page);
  await expect(page).toHaveURL(/\/en\/page\/7\/\?sort=name$/);
  await expect(page.getByTestId('sort-select')).toHaveValue('name');
  await expect(page.getByTestId('sample-input')).toHaveValue('ABC 123');
  await expect(page.getByTestId('zoom-select')).toHaveValue('3');
  await expect(top.getByTestId('page-edit')).toHaveCount(1);
  await expect(top.locator('.page-edit:first-child + [data-testid="page-prev"]')).toHaveCount(1);
  await expect(top.locator('.gap[aria-hidden="true"] svg.lucide-ellipsis')).toHaveCount(2);

  await page.setViewportSize({ width: 300, height: 800 });
  const bottom = page.getByTestId('pagination').last();
  await bottom.getByTestId('page-edit').last().click();
  await expect(bottom.getByTestId('page-input')).toHaveValue('7');
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(300);
  await bottom.getByTestId('page-input').fill('1');
  await bottom.getByTestId('page-input').press('Enter');
  await ready(page);
  await expect(page).toHaveURL(/\/en\/\?sort=name$/);
});

test('page editing validates bounds and integers and cancels with Escape or blur', async ({ page }) => {
  await page.goto('zh/page/8/');
  await ready(page);
  const top = page.getByTestId('pagination').first();
  const pencil = top.getByTestId('page-edit').last();
  await expect(pencil).toHaveAttribute('title', '编辑页码');
  await pencil.click();
  const input = top.getByTestId('page-input');
  for (const value of ['', '0', '99999', '2.5']) {
    await input.fill(value);
    await input.press('Enter');
    await expect(page).toHaveURL(/\/zh\/page\/8\/$/);
    await expect(input).toBeFocused();
    expect(await input.evaluate(el => (el as HTMLInputElement).validity.valid)).toBe(false);
  }
  await input.press('Escape');
  await expect(input).toHaveCount(0);
  await expect(pencil).toBeFocused();
  await pencil.click();
  await input.fill('3');
  await page.getByTestId('result-count').click();
  await expect(input).toHaveCount(0);
  await expect(page).toHaveURL(/\/zh\/page\/8\/$/);
});

test('sort and filters reset the page, while links and reload retain the selected filters', async ({ page }) => {
  await page.goto('en/page/3/');
  await ready(page);
  await page.getByTestId('sort-select').selectOption('name');
  await expect(page).toHaveURL(/\/en\/\?sort=name$/);
  await page.getByTestId('page-next').first().click();
  await ready(page);
  await expect(page).toHaveURL(/\/en\/page\/2\/\?sort=name$/);
  await expect(page.getByTestId('sort-select')).toHaveValue('name');
  const names = await slugs(page);
  await page.reload();
  await ready(page);
  expect(await slugs(page)).toEqual(names);
  await page.getByTestId('search-input').fill('fusion-pixel');
  await expect(page.locator(cards)).toHaveCount(1);
  await expect(page).toHaveURL(/\/en\/\?q=fusion-pixel&sort=name$/);
  await expect(page.locator('link[rel="canonical"]')).toHaveAttribute('href', 'https://fontpixel.com/en/');
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute('content', 'noindex, follow');
  await expect(page.getByTestId('pagination')).toHaveCount(0);
});

test('coverage URL state is restored rather than cleared during hydration', async ({ page }) => {
  await page.goto('en/?cov=gb2312:0.9');
  await ready(page);
  await expect(page.getByTestId('coverage-charset')).toHaveValue('gb2312');
  await expect(page.getByTestId('coverage-pct')).toHaveValue('90');
  await page.getByTestId('page-next').first().click();
  await ready(page);
  await expect(page.getByTestId('coverage-charset')).toHaveValue('gb2312');
  await expect(page).toHaveURL(/\/en\/page\/2\/\?cov=gb2312/);
});

test('reverse sorting persists through pagination and the last page has no next control', async ({ page, request }) => {
  const index = await (await request.get('/data/index.json')).json();
  const reversed = ratingOrder(index.families, index.charsetIds).reverse().map(f => f.slug);
  const totalPages = Math.ceil(reversed.length / 24);
  await page.goto('en/');
  await ready(page);
  await page.getByTestId('sort-select').selectOption('rating-reverse');
  await expect(page).toHaveURL(/sort=rating-reverse$/);
  expect(await slugs(page)).toEqual(reversed.slice(0, 24));
  await page.getByTestId('page-next').first().click();
  await ready(page);
  await expect(page.getByTestId('sort-select')).toHaveValue('rating-reverse');
  expect(await slugs(page)).toEqual(reversed.slice(24, 48));
  await page.getByTestId('pagination').first().locator(`[data-page="${totalPages}"]`).click();
  await ready(page);
  await expect(page.getByTestId('page-next')).toHaveCount(0);
  await expect(page.getByTestId('page-prev').first()).toBeVisible();
  await expect(page.getByTestId('pagination').first().locator('.page-edit:first-child')).toBeVisible();
  expect(await slugs(page)).toEqual(reversed.slice((totalPages - 1) * 24));
});

test('custom specimen and zoom persist when turning pages', async ({ page }) => {
  await page.goto('en/');
  await ready(page);
  await page.getByTestId('sample-input').fill('ABC 123');
  await page.getByTestId('zoom-select').selectOption('3');
  await page.getByTestId('page-next').first().click();
  await ready(page);
  await expect(page.getByTestId('sample-input')).toHaveValue('ABC 123');
  await expect(page.getByTestId('zoom-select')).toHaveValue('3');
  await expect(page.locator(`${cards} .card__sample canvas`).first()).toBeVisible();
});

test('language switching preserves the current page and build order', async ({ page }) => {
  await page.goto('en/page/2/');
  await ready(page);
  const order = await slugs(page);
  await page.getByTestId('lang-menu').locator('.navmenu__trigger').click();
  await page.getByTestId('lang-switch').click();
  await ready(page);
  await expect(page).toHaveURL(/\/zh\/page\/2\/$/);
  await expect(page.getByTestId('sort-select').locator('option[value="rating"]')).toHaveText('自动');
  expect(await slugs(page)).toEqual(order);
});

test('legacy random URLs become the fixed rating and returning from another sort restores it', async ({ page }) => {
  await page.goto('en/?sort=random');
  await ready(page);
  await expect(page.getByTestId('sort-select')).toHaveValue('rating');
  await expect(page).toHaveURL(/\/en\/$/);
  const order = await slugs(page);
  await page.getByTestId('sort-select').selectOption('name');
  await page.getByTestId('sort-select').selectOption('rating');
  expect(await slugs(page)).toEqual(order);
});
