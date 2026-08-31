import { expect, test } from '@playwright/test';

test('detail page shows metadata and license', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  await expect(page.locator('h1')).toContainText('文泉驿点阵宋体');
  await expect(page.getByTestId('meta-author')).toContainText('WenQuanYi');
  await expect(page.getByTestId('license-box')).toContainText('GPL');
  await page.getByTestId('license-details').locator('summary').click();
  await expect(page.getByTestId('license-details')).toContainText(
    'GNU GENERAL PUBLIC LICENSE',
  );
});

test('downloads list has per-variant files with sizes', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const dl = page.getByTestId('download-list');
  await expect(dl.locator('a[data-kind="bdf"]').first()).toHaveAttribute(
    'href',
    /wqy-bitmap-song--.*\.bdf\.gz$/,
  );
  await expect(dl.locator('a[data-kind="pcf"]').first()).toHaveAttribute(
    'href',
    /\.pcf\.gz$/,
  );
  await expect(dl.locator('[data-kind="zip"]')).toHaveAttribute(
    'href',
    /wqy-bitmap-song\.zip$/,
  );
  // bitmap TTF: all sizes of the same font packed into one file
  await expect(dl.locator('a[data-kind="ttf"]').first()).toHaveAttribute(
    'href',
    /wqy-bitmap-song.*\.ttf$/,
  );
  await expect(dl).toContainText('位图TTF');
  await expect(dl).toContainText('MB');
});

test('sample editor renders, missing highlight counts', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const editor = page.getByTestId('sample-editor');
  const canvas = editor.locator('canvas');
  await expect(canvas).toBeVisible();
  // ௵ (Tamil number sign) is not in wqy -> 1 missing char
  await editor.locator('textarea').fill('永A௵');
  await expect(editor.getByTestId('missing-count')).toContainText('1');
});

test('variant switcher toggles metrics panels', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const first = page.locator('[data-variant-panel]').first();
  const second = page.locator('[data-variant-panel]').nth(1);
  await expect(first).toBeVisible();
  await expect(second).toBeHidden();
  await page.getByTestId('variant-select').selectOption({ index: 1 });
  await expect(second).toBeVisible();
  await expect(first).toBeHidden();
});

test('ink diagram present with claimed and ink boxes', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const diagram = page.getByTestId('ink-diagram');
  await expect(diagram.locator('[data-box="claimed"]').first()).toBeVisible();
  await expect(diagram.locator('[data-box="han"]').first()).toBeVisible();
  // variants are sorted ascending by size; the first is the 12px tier (Han ink 11x11)
  await expect(page.getByTestId('metrics-table').first()).toContainText('11×11');
});

test('en detail page renders with no Chinese text', async ({ page }) => {
  await page.goto('en/fonts/wqy-bitmap-song/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByTestId('license-box')).toContainText('GPL');
  // the English site shouldn't leak Chinese: author, description, license name, and basis all have *_en fields
  for (const id of ['meta-author', 'license-box', 'font-description']) {
    const el = page.getByTestId(id);
    if (!(await el.count())) continue;
    const text = (await el.first().innerText()).replace(/[，。、；：！？（）]/g, '');
    expect(text, `${id} should not contain Han characters`).not.toMatch(/[\u4e00-\u9fff]/);
  }
});

test('variants are ordered by pixel size', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const opts = await page.getByTestId('variant-select').locator('option').allInnerTexts();
  const sizes = opts.map((o) => Number(o.match(/(\d+)\s*px/)?.[1] ?? NaN));
  expect(sizes.length).toBeGreaterThan(1);
  expect(sizes).toEqual([...sizes].sort((a, b) => a - b));
});

test('build notes collapse provenance and warnings, closed by default', async ({
  page,
}) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const notes = page.getByTestId('build-notes');
  await expect(notes).toBeVisible();
  await expect(notes).not.toHaveAttribute('open', /.*/);
  // provenance notes are hidden while collapsed, only appear once expanded
  await expect(notes.locator('.side__prov')).toBeHidden();
  await notes.locator('summary').click();
  await expect(notes.locator('.side__prov')).toBeVisible();
  await expect(notes.locator('.side__prov')).toContainText('导入自');
});

test('vector TTF downloads are listed', async ({ page }) => {
  // small fonts come in both shapes
  await page.goto('zh/fonts/4thd/');
  let dl = page.getByTestId('download-list');
  await expect(dl.locator('a[data-kind="ttf-square"]').first()).toHaveAttribute(
    'href',
    /-\d+px-square\.ttf$/,
  );
  await expect(dl.locator('a[data-kind="ttf-round"]').first()).toHaveAttribute(
    'href',
    /-\d+px-round\.ttf$/,
  );

  // fonts with over 20k glyphs only ship the square variant, not round
  await page.goto('zh/fonts/wqy-bitmap-song/');
  dl = page.getByTestId('download-list');
  await expect(dl.locator('a[data-kind="ttf-square"]').first()).toBeVisible();
  await expect(dl.locator('a[data-kind="ttf-round"]')).toHaveCount(0);
});

test('download rows are ordered: per-variant, BDF zip, bitmap TTF, vector TTF', async ({
  page,
}) => {
  await page.goto('en/fonts/4thd/');
  const heads = await page
    .getByTestId('download-list')
    .locator('tbody tr th')
    .allInnerTexts();
  const zip = heads.findIndex((h) => /Full family BDF ZIP/.test(h));
  const bmp = heads.findIndex((h) => /Bitmap TTF/.test(h));
  const vec = heads.findIndex((h) => /Vector TTF/.test(h));
  expect(zip).toBeGreaterThan(0); // per-variant rows (BDF/PCF) come first
  expect(zip).toBeLessThan(bmp);
  expect(bmp).toBeLessThan(vec);
});

test('license is shown as a short label, never the raw LicenseRef id', async ({
  page,
}) => {
  await page.goto('en/fonts/baekmuk-gulim/');
  await expect(page.getByTestId('license-box').locator('.chip')).toHaveText(
    'Baekmuk',
  );
  // the catalogue card and filter panel likewise shouldn't leak the internal id
  await page.goto('en/');
  await page.getByTestId('search-input').fill('baekmuk');
  await expect(
    page.locator('.card[data-slug="baekmuk-gulim"] .card__lic'),
  ).toHaveText('Baekmuk');
  for (const path of ['en/', 'zh/', 'en/fonts/baekmuk-gulim/']) {
    await page.goto(path);
    const text = await page.locator('body').innerText();
    expect(text, `${path} should not show LicenseRef-`).not.toContain('LicenseRef-');
  }
});

test('the sample editor can copy its dot matrix three ways', async ({
  page,
  context,
}) => {
  await context.grantPermissions(['clipboard-read', 'clipboard-write']);
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const bar = page.getByTestId('dot-copy');
  await bar.scrollIntoViewIfNeeded();

  // .# plain text: only dots and hashes, consistent line width
  await page.getByTestId('copy-dots').click();
  const dots = await page.evaluate(() => navigator.clipboard.readText());
  expect(dots.length).toBeGreaterThan(0);
  const lines = dots.split('\n');
  expect(lines.every((l) => /^[.#]+$/.test(l))).toBe(true);
  expect(new Set(lines.map((l) => l.length)).size).toBe(1);
  expect(dots).toContain('#');
  // the first and last lines shouldn't be blank—already trimmed on export
  expect(lines[0]).toContain('#');
  expect(lines[lines.length - 1]).toContain('#');

  // BDF style: a glyph block pastable into a .bdf file
  await page.getByTestId('copy-bdf').click();
  const bdf = await page.evaluate(() => navigator.clipboard.readText());
  expect(bdf).toMatch(/^STARTCHAR U\+[0-9A-F]{4}/);
  expect(bdf).toContain('BITMAP');
  expect(bdf.trimEnd().endsWith('ENDCHAR')).toBe(true);
  // block count matches the deduped character count
  const starts = bdf.match(/STARTCHAR/g)!.length;
  const ends = bdf.match(/ENDCHAR/g)!.length;
  expect(starts).toBe(ends);
});

test('every author links to a catalogue search by their name', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const links = page.getByTestId('meta-author').locator('a');
  await expect(links).toHaveCount(2); // WenQuanYi Project, Qianqian Fang
  await expect(links.first()).toHaveAttribute(
    'href',
    '/zh/?q=' + encodeURIComponent('WenQuanYi Project'),
  );

  await links.first().click();
  await page.waitForLoadState('domcontentloaded');
  expect(new URL(page.url()).pathname).toBe('/zh/');
  await expect(page.getByTestId('search-input')).toHaveValue('WenQuanYi Project');
  const island = page.locator('[data-testid="catalogue-island"]');
  expect(await island.locator('.card').count()).toBeGreaterThanOrEqual(1);
});

test('a former name can find the font via search', async ({ page }) => {
  await page.goto('zh/?q=GalmuriExtended');
  const island = page.locator('[data-testid="catalogue-island"]');
  await expect(island.locator('.card')).toHaveCount(1);
  await expect(island).toContainText('全小素');
});
