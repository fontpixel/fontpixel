import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';

const index = JSON.parse(readFileSync('public/data/index.json', 'utf8'));
const family = (slug: string) => index.families.find((f: { slug: string }) => f.slug === slug);

test('catalogue cards mark which variants meet the per-variant filters', async ({ page }) => {
  // misc-fixed: only its 18×18 faces write Simplified Chinese.
  await page.goto('en/?q=misc%20fixed&scripts=zh-hans');
  const card = page.locator('[data-slug="misc-fixed"]');
  const mark = card.getByTestId('variant-mark');
  await expect(mark).toHaveAttribute('data-variant-mark', 'some');
  const title = await mark.getAttribute('title');
  expect(title).toMatch(/^Some variants: /);
  expect(title).toContain('18px');
  expect(title).not.toContain('13px');

  // Every WenQuanYi Bitmap Song size writes Simplified Chinese.
  await page.goto('en/?q=wenquanyi&scripts=zh-hans');
  await expect(page.locator('[data-slug="wqy-bitmap-song"]').getByTestId('variant-mark'))
    .toHaveAttribute('title', 'All variants');

  // No per-variant filter, no mark.
  await page.goto('en/?q=misc%20fixed');
  await expect(page.locator('[data-slug="misc-fixed"]')).toBeVisible();
  await expect(page.getByTestId('variant-mark')).toHaveCount(0);
});

test('single-variant families never show a mark', async ({ page }) => {
  const single = index.families.find((f: { variants: unknown[]; scripts: string[] }) =>
    f.variants.length === 1 && f.scripts.includes('latin'));
  await page.goto(`en/?q=${single.slug}&scripts=latin`);
  await expect(page.locator(`[data-slug="${single.slug}"]`)).toBeVisible();
  await expect(page.locator(`[data-slug="${single.slug}"] [data-testid="variant-mark"]`)).toHaveCount(0);
  await page.goto(`en/fonts/${single.slug}/`);
  await expect(page.locator('[data-script="latin"]')).toBeVisible();
  await expect(page.getByTestId('variant-mark')).toHaveCount(0);
});

test('a size and a script from different variants no longer combine', async ({ page }) => {
  // misc-fixed has 13px faces and Simplified Chinese faces, but no 13px one
  // writes Simplified Chinese.
  await page.goto('en/?q=misc%20fixed&scripts=zh-hans&sizes=13');
  await expect(page.getByTestId('result-count')).toHaveText(/^\s*0\D/);
  await page.goto('en/?q=misc%20fixed&scripts=zh-hans&sizes=18');
  await expect(page.locator('[data-slug="misc-fixed"] [data-testid="variant-mark"]'))
    .toHaveAttribute('data-variant-mark', 'some');
});

test('coverage and character filters are judged per variant once their data loads', async ({ page }) => {
  await page.goto('en/?q=misc%20fixed&cov=gb2312:0.9');
  const mark = page.locator('[data-slug="misc-fixed"] [data-testid="variant-mark"]');
  await expect(mark).toHaveAttribute('data-variant-mark', 'some');
  expect(await mark.getAttribute('title')).toContain('18px');
  await page.goto(`en/?q=misc%20fixed&chars=${encodeURIComponent('张')}`);
  await expect(mark).toHaveAttribute('data-variant-mark', 'some');
  expect(await mark.getAttribute('title')).not.toContain('13px');
});

test('script labels on the detail page mark the variants that earn them', async ({ page }) => {
  await page.goto('en/fonts/misc-fixed/');
  const variants = family('misc-fixed').variants as { scripts: string[] }[];
  for (const script of family('misc-fixed').scripts as string[]) {
    const mark = page.locator(`[data-script="${script}"] + [data-testid="variant-mark"]`);
    const all = variants.every((v) => v.scripts.includes(script));
    await expect(mark).toHaveAttribute('data-variant-mark', all ? 'all' : 'some');
  }
  const zh = page.locator('[data-script="zh-hans"] + [data-testid="variant-mark"]');
  expect(await zh.getAttribute('title')).toContain('18px');
});
