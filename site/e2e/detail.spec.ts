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
  // 位图 TTF：同一字体的全部尺寸打进一个文件
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
  // ௵(泰米尔文数字符号)不在 wqy 里 → 缺 1 字
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
  // 变体按尺寸升序，首个是 12px 那档（汉字墨迹 11×11）
  await expect(page.getByTestId('metrics-table').first()).toContainText('11×11');
});

test('en detail page renders with no Chinese text', async ({ page }) => {
  await page.goto('en/fonts/wqy-bitmap-song/');
  await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  await expect(page.getByTestId('license-box')).toContainText('GPL');
  // 英文站不该漏出中文：作者、简介、许可证名与授权依据都有 *_en 字段
  for (const id of ['meta-author', 'license-box', 'font-description']) {
    const el = page.getByTestId(id);
    if (!(await el.count())) continue;
    const text = (await el.first().innerText()).replace(/[，。、；：！？（）]/g, '');
    expect(text, `${id} 不应出现汉字`).not.toMatch(/[\u4e00-\u9fff]/);
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
  // 折叠时来源说明不可见，展开后才出现
  await expect(notes.locator('.side__prov')).toBeHidden();
  await notes.locator('summary').click();
  await expect(notes.locator('.side__prov')).toBeVisible();
  await expect(notes.locator('.side__prov')).toContainText('导入自');
});

test('vector TTF downloads are listed', async ({ page }) => {
  // 小字体两种造型都有
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

  // 字形数超过 2 万的只出方点版，不出圆点
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
  expect(zip).toBeGreaterThan(0); // 变体行（BDF/PCF）排在最前
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
  // 目录页卡片与筛选面板同样不该露出内部 id
  await page.goto('en/');
  await page.getByTestId('search-input').fill('baekmuk');
  await expect(
    page.locator('.card[data-slug="baekmuk-gulim"] .card__lic'),
  ).toHaveText('Baekmuk');
  for (const path of ['en/', 'zh/', 'en/fonts/baekmuk-gulim/']) {
    await page.goto(path);
    const text = await page.locator('body').innerText();
    expect(text, `${path} 不该出现 LicenseRef-`).not.toContain('LicenseRef-');
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

  // .# 纯文本：只含点与井号，行宽一致
  await page.getByTestId('copy-dots').click();
  const dots = await page.evaluate(() => navigator.clipboard.readText());
  expect(dots.length).toBeGreaterThan(0);
  const lines = dots.split('\n');
  expect(lines.every((l) => /^[.#]+$/.test(l))).toBe(true);
  expect(new Set(lines.map((l) => l.length)).size).toBe(1);
  expect(dots).toContain('#');
  // 首末行不应是空行——导出时已裁掉
  expect(lines[0]).toContain('#');
  expect(lines[lines.length - 1]).toContain('#');

  // BDF 风格：可粘进 .bdf 的字形段
  await page.getByTestId('copy-bdf').click();
  const bdf = await page.evaluate(() => navigator.clipboard.readText());
  expect(bdf).toMatch(/^STARTCHAR U\+[0-9A-F]{4}/);
  expect(bdf).toContain('BITMAP');
  expect(bdf.trimEnd().endsWith('ENDCHAR')).toBe(true);
  // 段数与去重后的字符数一致
  const starts = bdf.match(/STARTCHAR/g)!.length;
  const ends = bdf.match(/ENDCHAR/g)!.length;
  expect(starts).toBe(ends);
});

test('每位作者都链到按其名字搜索的目录页', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const links = page.getByTestId('meta-author').locator('a');
  await expect(links).toHaveCount(2); // WenQuanYi Project、Qianqian Fang
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

test('曾用名能搜到字体', async ({ page }) => {
  await page.goto('zh/?q=GalmuriExtended');
  const island = page.locator('[data-testid="catalogue-island"]');
  await expect(island.locator('.card')).toHaveCount(1);
  await expect(island).toContainText('全小素');
});
