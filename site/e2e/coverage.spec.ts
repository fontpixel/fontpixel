import { expect, test } from '@playwright/test';

test('coverage report shows charset rows with denominators', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const report = page.getByTestId('coverage-report');
  const gbRow = report.locator(
    '[data-variant-panel]:not([hidden]) [data-charset="gb2312"]',
  );
  await expect(gbRow).toContainText('GB/T 2312');
  await expect(gbRow).toContainText('6,763 / 6,763');
  await expect(gbRow).toContainText('完整');
  await expect(report).toContainText('已编码字符');
  await expect(report).toContainText('GB 18030-2022 实现级别 1');
});

test('missing chars expandable for small sets', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  // 注音符号 41/75:缺 34,可展开
  const row = page.locator(
    '[data-variant-panel]:not([hidden]) [data-charset="bopomofo"]',
  );
  await row.scrollIntoViewIfNeeded();
  await row.locator('summary').click();
  const chars = row.locator('.cov__missing-chars');
  await expect(chars).toBeVisible();
  expect((await chars.textContent())!.length).toBeGreaterThan(10);
});

test('coverage switches with variant', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const panels = page.getByTestId('coverage-report').locator('[data-variant-panel]');
  await expect(panels.first()).toBeVisible();
  await expect(panels.nth(1)).toBeHidden();
  await page.getByTestId('variant-select').selectOption({ index: 1 });
  await expect(panels.nth(1)).toBeVisible();
});

test('glyph grid renders sheets and inspector', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const sheet = grid.locator('.gg__sheet canvas').first();
  await expect(sheet).toBeVisible();
  await expect
    .poll(() => sheet.evaluate((c: HTMLCanvasElement) => c.dataset['cell'] ?? ''))
    .not.toBe('');
  const cell = await sheet.evaluate((c: HTMLCanvasElement) => Number(c.dataset['cell']));
  const block = await sheet.evaluate((c: HTMLCanvasElement) => Number(c.dataset['block']));
  // 点击首个区块内的 'A'(若在)或该块首个存在的格子:用 A 所在 block 0 canvas
  const rect = await sheet.boundingBox();
  const scale = rect!.width / (16 * cell);
  const target = 0x41 - block; // block 0 时为 65
  const col = target % 16;
  const row = Math.floor(target / 16);
  await sheet.click({
    position: { x: (col * cell + cell / 2) * scale, y: (row * cell + cell / 2) * scale },
  });
  const inspector = page.getByTestId('glyph-inspector');
  await expect(inspector).toBeVisible();
  await expect(inspector).toContainText('U+0041');
});

test('char lookup filters catalogue', async ({ page }) => {
  await page.goto('zh/');
  const countOf = async () => {
    const t = await page.getByTestId('result-count').textContent();
    return Number.parseInt(t!.match(/\d+/)![0], 10);
  };
  const all = await countOf();
  await page.getByTestId('chars-input').fill('永');
  await expect.poll(countOf).toBeLessThanOrEqual(all);
  expect(await countOf()).toBeGreaterThanOrEqual(4); // 五家族中至少 4 家有「永」
  await page.getByTestId('chars-input').fill('͸'); // U+0378 未指派——但 Unifont 连它都有
  await expect.poll(countOf).toBeLessThanOrEqual(1);
  await page.getByTestId('chars-input').fill('\u{40000}'); // 第 4 平面,任何字体都不会编码
  await expect.poll(countOf).toBe(0);
  await expect(page.getByTestId('catalogue-island')).toContainText('没有符合条件的字体');
});
