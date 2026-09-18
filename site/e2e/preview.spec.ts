import { expect, test } from '@playwright/test';

const specimens = [
  { slug: 'fusion-pixel', suffix: 'zh_hant', text: '落霞與孤鶩齊飛，秋水共長天一色。' },
  { slug: 'fusion-bold-pixel', suffix: 'zh_hant', text: '落霞與孤鶩齊飛，秋水共長天一色。' },
  { slug: 'ark-pixel', suffix: 'ja', text: '色は匂へど 散りぬるを 我が世誰ぞ 常ならむ' },
  { slug: 'jelly-pixel', suffix: 'latin', text: 'Sphinx of black quartz, judge my vow. 0123456789' },
];

test('Dylex defaults to its most complete 8–16px variant on cards and detail', async ({ page }) => {
  await page.goto('en/?q=dylex-terminal');
  const card = page.locator('[data-slug="dylex-terminal"]');
  await expect(card).toHaveAttribute('data-variant-id', '7x13');
  await card.locator('a').click();
  await expect(page.getByTestId('variant-select')).toHaveValue('7x13');
  await expect(page.getByTestId('coverage-variant')).toHaveValue('7x13');
  await expect(page.locator('.hero__preview')).toHaveAttribute('data-variant-id', '7x13');
  await page.getByTestId('variant-select').selectOption('10x20');
  await expect(page.getByTestId('variant-select')).toHaveValue('10x20');
  await expect(page.getByTestId('sample-editor').locator('canvas').first()).toBeVisible();
});

for (const { slug, suffix, text } of specimens) {
  for (const lang of ['en', 'zh']) {
    test(`${slug} keeps its default sample and matching variant on ${lang} cards and detail`, async ({ page }) => {
      const variant = `${slug}-12px-proportional-${suffix}`;
      const fontRequests: string[] = [];
      page.on('request', (r) => { if (r.url().includes('.bdf.gz') || r.url().includes('/packs/')) fontRequests.push(r.url()); });
      await page.goto(`${lang}/?q=${slug}`);
      const card = page.locator(`[data-testid="catalogue-island"] [data-slug="${slug}"]`);
      await card.scrollIntoViewIfNeeded();
      await expect(card).toHaveAttribute('data-variant-id', variant);
      await expect(card.locator('.card__sample svg')).toBeVisible();
      expect(fontRequests).toEqual([]);

      await card.locator('a').click();
      await expect(page.getByTestId('variant-select')).toHaveValue(variant);
      await expect(page.getByTestId('coverage-variant')).toHaveValue(variant);
      await expect(page.locator('.hero__preview')).toHaveAttribute('data-variant-id', variant);
      const sample = page.getByTestId('sample-editor');
      await expect(sample.locator('textarea')).toHaveValue(text);
      await expect(sample.getByTestId('missing-count')).toHaveCount(0);
      await expect(page.locator('.compare-link a')).toHaveAttribute('href', `/${lang}/compare/?v=${slug}:${variant}`);
    });
  }
}

for (const lang of ['zh-Hant', 'ja', 'ko', 'fr']) {
  test(`fusion-pixel keeps its Traditional Chinese sample on the ${lang} page`, async ({ page }) => {
    const variant = 'fusion-pixel-12px-proportional-zh_hant';
    await page.goto(`${lang}/fonts/fusion-pixel/`);
    await expect(page.getByTestId('variant-select')).toHaveValue(variant);
    await expect(page.getByTestId('coverage-variant')).toHaveValue(variant);
    await expect(page.locator('.hero__preview')).toHaveAttribute('data-variant-id', variant);
    await expect(page.getByTestId('sample-editor').locator('textarea')).toHaveValue(specimens[0]!.text);
  });
}

for (const lang of ['en', 'zh']) {
  test(`comparison uses the family default on ${lang} and preserves explicit variant links`, async ({ page }) => {
    await page.goto(`${lang}/compare/?v=fusion-pixel`);
    await expect(page).toHaveURL(/v=fusion-pixel%3Afusion-pixel-12px-proportional-zh_hant/);
    await expect(page.getByTestId('compare').locator('textarea')).toHaveValue(specimens[0]!.text);
    await page.goto(`${lang}/compare/?v=fusion-pixel:fusion-pixel-12px-proportional-ja`);
    await expect(page).toHaveURL(/v=fusion-pixel%3Afusion-pixel-12px-proportional-ja/);
  });
}
