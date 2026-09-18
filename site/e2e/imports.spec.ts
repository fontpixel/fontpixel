import { expect, test } from '@playwright/test';
import { gunzipSync } from 'node:zlib';

for (const font of [
  { slug: 'font8x8', name: 'font8x8', author: 'Marcel Sondaar', license: /Public [Dd]omain/, glyphs: 599 },
]) {
  test(`${font.slug} is searchable with credits, preview, and downloadable BDF`, async ({ page, request }) => {
    await page.goto(`en/?q=${font.slug}`);
    const card = page.locator(`[data-testid="catalogue-island"] [data-slug="${font.slug}"]`);
    await expect(card).toBeVisible();
    await card.locator('a').click();
    await expect(page.locator('h1')).toHaveText(font.name);
    await expect(page.getByTestId('meta-author').locator('a').first()).toHaveText(font.author);
    await expect(page.getByTestId('license-box')).toContainText(font.license);
    await expect(page.getByTestId('sample-editor').locator('canvas').first()).toBeVisible();
    const href = await page.getByTestId('download-list').locator('a[data-kind="bdf"]').first().getAttribute('href');
    const response = await request.get(href!);
    expect(response.ok()).toBe(true);
    const body = await response.body();
    // Astro preview sets Content-Encoding: gzip; Playwright then decompresses it.
    const bdf = body[0] === 0x1f && body[1] === 0x8b ? gunzipSync(body) : body;
    expect(bdf.toString()).toContain(`CHARS ${font.glyphs}\n`);
  });
}

test('Press Start 2P reports complete Greek and Cyrillic coverage and renders both', async ({ page }) => {
  await page.goto('en/fonts/press-start-2p/');
  const coverage = page.getByTestId('coverage-report');
  await expect(coverage.locator('[data-charset="greek"]')).toContainText('72 / 72');
  await expect(coverage.locator('[data-charset="cyrillic"]')).toContainText('97 / 97');
  const editor = page.getByTestId('sample-editor');
  await expect(page.getByTestId('variant-select')).toHaveValue('PressStart2P-Regular-8px');
  for (const preset of ['Greek', 'Cyrillic']) {
    await editor.locator('textarea').fill('𰻞');
    await expect(editor.getByTestId('missing-count')).toContainText('1');
    await editor.getByRole('button', { name: preset, exact: true }).click();
    await expect(editor.getByTestId('missing-count')).toHaveCount(0);
  }
});

test('Poxiao Pixel includes only the regular build and removes duplicate Hax downloads', async ({ page, request }) => {
  await page.goto('zh/fonts/poxiao-pixel/');
  const variants = page.getByTestId('variant-select');
  await expect(variants.locator('option')).toHaveCount(1);
  await expect(variants).toHaveValue('PoxiaoPixel-CN-12px');
  await expect(page.locator('main')).toContainText('由于技术原因，本站仅收录普通版本。');
  const downloads = page.getByTestId('download-list');
  await expect(downloads.locator('a[href*="Hax"]')).toHaveCount(0);
  expect((await request.get('/downloads/poxiao-pixel--PoxiaoPixel-Hax-12px.bdf.gz')).status()).toBe(404);
  expect((await request.get('/downloads/poxiao-pixel--PoxiaoPixel-Hax-12px.pcf.gz')).status()).toBe(404);
  expect((await request.get('/downloads/poxiao-pixel--PoxiaoPixel-CN-12px.bdf.gz')).ok()).toBe(true);
});

test('MuzaiPixel has one native variant and its full block survives preview and download', async ({ page, request }) => {
  await page.goto('en/fonts/muzai-pixel/');
  const variants = page.getByTestId('variant-select');
  await expect(variants.locator('option')).toHaveCount(1);
  await expect(variants).toHaveValue('MuzaiPixel');
  const editor = page.getByTestId('sample-editor');
  await expect(editor.locator('textarea')).not.toHaveValue('');
  await editor.locator('textarea').fill('▆▇█▉▊●ニ二');
  await expect(editor.getByTestId('missing-count')).toHaveCount(0);
  await expect(editor.locator('canvas').first()).toBeVisible();

  const downloads = page.getByTestId('download-list');
  await expect(downloads.locator('a[href*="MuzaiPixel-12px"]')).toHaveCount(0);
  const href = await downloads.locator('a[data-kind="bdf"]').first().getAttribute('href');
  const response = await request.get(href!);
  expect(response.ok()).toBe(true);
  const bytes = await response.body();
  const text = (bytes[0] === 0x1f && bytes[1] === 0x8b ? gunzipSync(bytes) : bytes).toString();
  expect(text).toContain('CHARS 15932\n');
  const block = text.split('STARTCHAR ').find((glyph) => glyph.includes('\nENCODING 9608\n'))!;
  expect(block).toContain('BBX 8 12 0 -2\n');
  expect(block.split('BITMAP\n')[1].split('ENDCHAR')[0]).toBe('FF\n'.repeat(12));

  // The duplicate must disappear from generated assets as well as the dropdown.
  expect((await request.get('/downloads/muzai-pixel--MuzaiPixel-12px.bdf.gz')).status()).toBe(404);
  expect((await request.get('/data/packs/muzai-pixel/MuzaiPixel-12px/manifest.json')).status()).toBe(404);
});
