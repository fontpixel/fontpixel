import { expect, test } from '@playwright/test';
import { gunzipSync } from 'node:zlib';

test('clearing the last Vibe keeps each group open until manually collapsed', async ({ page }) => {
  await page.goto('en/');
  const groups = page.locator('details.vibe-group');
  expect(await groups.count()).toBe(5);
  for (const group of await groups.all()) {
    await group.locator('summary').click();
    const tag = group.locator('button').first();
    await tag.click();
    await expect(tag).toHaveClass(/\bon\b/);
    await tag.click();
    await expect(tag).not.toHaveClass(/\bon\b/);
    await expect(group).toHaveAttribute('open', '');
    await expect(tag).toBeVisible();
    await group.locator('summary').click();
    await expect(group).not.toHaveAttribute('open');
  }
});

test('fine Vibes filter the catalogue and survive the URL', async ({ page }) => {
  await page.goto('en/');
  const group = page.locator('details.vibe-group').filter({ hasText: 'Print & manuscripts' });
  await group.locator('summary').click();
  await group.getByRole('button', { name: 'Uncial', exact: true }).click();
  await expect(page.locator('[data-slug="scriptorium"]')).toBeVisible();
  await expect(page).toHaveURL(/uncial/);
  await page.reload();
  await expect(page.locator('[data-slug="scriptorium"]')).toBeVisible();
  await expect(page.locator('[data-slug="home-video"]')).toHaveCount(0);
});

for (const slug of ['pixtura12', 'pixelzone', 'not-jam-blackletter', 'frogatto-dialog', 'gilded-bitmap', 'dank-depths', 'fantasy-warrior', '1307']) {
  test(`${slug} offers a working preview and BDF download`, async ({ page, request }) => {
    await page.goto(`en/fonts/${slug}/`);
    await expect(page.getByTestId('sample-editor').locator('canvas').first()).toBeVisible();
    const href = await page.getByTestId('download-list').locator('a[data-kind="bdf"]').first().getAttribute('href');
    expect((await request.get(href!)).ok()).toBe(true);
    await expect(page.locator('.side__list')).toContainText(/Bitmap source|Pixel outlines/);
  });
}

test('Fantasy Warrior retains every modern Hangul syllable and previews Korean', async ({ page, request }) => {
  await page.goto('en/fonts/fantasy-warrior/');
  const editor = page.getByTestId('sample-editor');
  await editor.locator('textarea').fill('한글 가나다라마 가나다라 ABC АБВ 0123');
  await expect(editor.getByTestId('missing-count')).toHaveCount(0);
  const response = await request.get('/data/details/fantasy-warrior.json');
  expect(response.ok()).toBe(true);
  const detail = await response.json();
  const variant = detail.meta.variants[0].id;
  expect(detail.coverage[variant]['hangul-syllables']).toEqual([11172, 11172]);
  expect(detail.meta.variants[0].glyphs).toBe(11716);
});

test('1307 BDF keeps the original ASCII map and all unencoded Pulp UI tiles', async ({ page, request }) => {
  await page.goto('en/fonts/1307/');
  const href = await page.getByTestId('download-list').locator('a[data-kind="bdf"]').first().getAttribute('href');
  const response = await request.get(href!);
  const bytes = await response.body();
  const text = (bytes[0] === 0x1f && bytes[1] === 0x8b ? gunzipSync(bytes) : bytes).toString();
  expect(text).toContain('CHARS 109\n');
  expect(text.match(/^ENCODING -1$/gm)).toHaveLength(14);
  expect(text).toContain('STARTCHAR pulp-ui-121\nENCODING -1\n');
  const encoded = [...text.matchAll(/^ENCODING (\d+)$/gm)].map(match => Number(match[1]));
  expect(encoded).toEqual(Array.from({ length: 95 }, (_, i) => i + 32));
});
