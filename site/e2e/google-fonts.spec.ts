import { expect, test } from '@playwright/test';
import { gunzipSync } from 'node:zlib';
import audit from '../../docs/audits/google-fonts-import-audit-2026-09-17.json' with { type: 'json' };
import secondAudit from '../../docs/audits/google-fonts-jacquard-jersey-handjet-audit-2026-09-17.json' with { type: 'json' };
import bitcountAudit from '../../docs/audits/bitcount-family-audit-2026-09-17.json' with { type: 'json' };

const allVariants = [
  ...audit.variants.filter((v) => !['bitcount', 'bitcount-single'].includes(v.family)),
  ...secondAudit.variants,
  ...bitcountAudit.variants,
];
for (const slug of new Set(allVariants.map((v) => v.family))) {
  test(`${slug} renders and downloads all official characters and unencoded glyphs`, async ({ page, request }) => {
    const variants = allVariants.filter((v) => v.family === slug);
    await page.goto(`en/fonts/${slug}/`);
    await expect(page.getByTestId('license-box')).toContainText('SIL Open Font License');
    const editor = page.getByTestId('sample-editor');
    const select = page.getByTestId('variant-select');
    await expect(select.locator('option')).toHaveCount(variants.length);
    await expect(editor.locator('textarea')).not.toHaveValue('');
    for (const variant of variants) {
      const id = variant.file.replace(/\.bdf$/, '');
      await select.selectOption(id);
      await expect(page.getByTestId('coverage-variant')).toHaveValue(id);
      await expect(editor.getByTestId('missing-count')).toHaveCount(0);
      await expect.poll(async () => Number(await editor.locator('canvas').first().getAttribute('width'))).toBeGreaterThan(0);

      const link = page.getByTestId('download-list').locator(`a[data-kind="bdf"][href$="${slug}--${id}.bdf.gz"]`);
      const href = await link.getAttribute('href');
      expect(href).toBeTruthy();
      const response = await request.get(href!);
      expect(response.ok()).toBe(true);
      const bytes = await response.body();
      const bdf = (bytes[0] === 0x1f && bytes[1] === 0x8b ? gunzipSync(bytes) : bytes).toString();
      const encodings = [...bdf.matchAll(/^ENCODING (-?\d+)$/gm)].map((m) => Number(m[1]));
      expect(encodings.filter((cp) => cp >= 0)).toHaveLength(variant.unicode_characters);
      expect(encodings.filter((cp) => cp === -1)).toHaveLength(variant.unencoded_glyphs);
    }
  });
}

test('Pixelify Sans retains Cyrillic in every imported weight', async ({ page }) => {
  await page.goto('en/fonts/pixelify-sans/');
  const editor = page.getByTestId('sample-editor');
  await expect(editor.locator('textarea')).not.toHaveValue('');
  await editor.locator('textarea').fill('ЖяЁёЇї');
  for (const weight of ['Regular', 'Medium', 'SemiBold', 'Bold']) {
    await page.getByTestId('variant-select').selectOption(`PixelifySans-${weight}-11px`);
    await expect(editor.getByTestId('missing-count')).toHaveCount(0);
  }
});

test('Handjet previews characters from all six official writing systems', async ({ page }) => {
  await page.goto('en/fonts/handjet/');
  const editor = page.getByTestId('sample-editor');
  const text = editor.locator('textarea');
  await expect(text).not.toHaveValue('');
  await text.fill('𰻞');
  await expect(editor.getByTestId('missing-count')).toContainText('1');
  await text.fill('Aa Ωω Жя Աա אב عا');
  await expect(editor.getByTestId('missing-count')).toHaveCount(0);
});

test('Bitcount defaults to Single and both former family pages redirect to it', async ({ page }) => {
  for (const lang of ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr']) {
    await page.goto(`${lang}/fonts/bitcount/`);
    await expect(page.getByTestId('variant-select')).toHaveValue('BitcountSingle-Regular-10px');
    await expect(page.getByTestId('coverage-variant')).toHaveValue('BitcountSingle-Regular-10px');
  }
  for (const slug of ['bitcount-single', 'bitcount-prop-single']) {
    await page.goto(`en/fonts/${slug}/`);
    await expect(page).toHaveURL(/\/en\/fonts\/bitcount\/?$/);
    await expect(page.getByTestId('variant-select')).toHaveValue('BitcountSingle-Regular-10px');
  }
  await page.goto('en/?q=Bitcount');
  const cards = page.getByTestId('catalogue-island').locator('.card');
  await expect(cards).toHaveCount(1);
  await expect(cards.first()).toHaveAttribute('data-slug', 'bitcount');
});

for (const [slug, names] of [
  ['jacquard', ['Jacquard 12', 'Jacquard 24']],
  ['jersey', ['Jersey 10', 'Jersey 15', 'Jersey 20', 'Jersey 25']],
] as const) {
  test(`${slug} sizes are searchable as one family`, async ({ page }) => {
    for (const name of names) {
      await page.goto(`en/?q=${encodeURIComponent(name)}`);
      const cards = page.getByTestId('catalogue-island').locator('.card');
      await expect(cards).toHaveCount(1);
      await expect(cards.first()).toHaveAttribute('data-slug', slug);
    }
  });
}
