import { expect, test } from '@playwright/test';

const corrections: Record<string, string[]> = {
  clfn: ['song', 'serif'],
  'nightgazer-bitmap': ['song', 'serif'],
  kappa20: ['song', 'serif'],
  'miraero-normal': ['kai'],
  'kh-dot-kabutochou': ['gothic', 'decorative', 'sans'],
  fashionbitmap16: ['gothic', 'decorative', 'sans'],
};

test('all categories use canonical values and include the broader category', async ({ request }) => {
  const index = await (await request.get('/data/index.json')).json();
  for (const font of index.families) {
    expect(font).not.toHaveProperty('form');
    expect(new Set(font.forms).size).toBe(font.forms.length);
    for (const old of ['round', 'mingcho', 'serif-pixel']) expect(font.forms).not.toContain(old);
    if (font.forms.includes('gothic')) expect(font.forms).toContain('sans');
    if (font.forms.includes('song')) expect(font.forms).toContain('serif');
    if (corrections[font.slug]) expect(font.forms).toEqual(corrections[font.slug]);
  }
});

test('corrected fonts show every category as a filter link', async ({ page }) => {
  for (const [slug, forms] of Object.entries(corrections)) {
    await page.goto(`en/fonts/${slug}/`);
    const links = page.locator('.side__list a[href*="?forms="]');
    await expect(links).toHaveCount(forms.length);
    expect(await links.evaluateAll(elements => elements.map(el => new URL((el as HTMLAnchorElement).href).searchParams.get('forms')))).toEqual(forms);
    if (forms.includes('song')) {
      await expect(links.filter({ hasText: 'Song / Mincho' })).toBeVisible();
      await expect(links.filter({ hasText: /^Serif$/ })).toBeVisible();
    }
  }
});

test('selecting several categories matches any category without duplicate results', async ({ page, request }) => {
  const index = await (await request.get('/data/index.json')).json();
  const expected = index.families.filter((f: { forms: string[] }) => f.forms.some(form => ['gothic', 'decorative'].includes(form)));
  await page.goto('en/?forms=gothic,decorative');
  await expect(page.locator('[data-form="gothic"]')).toHaveClass(/\bon\b/);
  await expect(page.locator('[data-form="decorative"]')).toHaveClass(/\bon\b/);
  await expect(page.getByTestId('result-count')).toContainText(`${expected.length} fonts`);
  const slugs = await page.locator('article.card').evaluateAll(cards => cards.map(card => card.getAttribute('data-slug')));
  expect(new Set(slugs).size).toBe(slugs.length);
  expect(slugs.every(slug => expected.some((f: { slug: string }) => f.slug === slug))).toBe(true);
  await expect(page.locator('[data-form="round"]')).toHaveCount(0);
  await expect(page.locator('[data-form="rounded"]')).toHaveCount(1);
  await page.getByTestId('search-input').fill('kh-dot-kabutochou');
  await expect(page.locator('article.card')).toHaveCount(1);
  await expect(page.locator('.card__meta')).toContainText('Gothic / Decorative / Sans-serif');
});

for (const [old, current] of Object.entries({ mingcho: 'song', round: 'rounded', 'serif-pixel': 'serif' })) {
  test(`old ${old} links use the ${current} category`, async ({ page }) => {
    await page.goto(`en/?forms=${old}`);
    await expect(page.locator(`[data-form="${current}"]`)).toHaveClass(/\bon\b/);
    await expect(page).toHaveURL(new RegExp(`\\?forms=${current}$`));
  });
}
