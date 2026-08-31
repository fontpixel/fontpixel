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

test('missing chars open from the row that owns them', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  // 注音符号 41/75：缺 34
  const row = page.locator(
    '[data-variant-panel]:not([hidden]) [data-charset="bopomofo"]',
  );
  await row.scrollIntoViewIfNeeded();
  await row.locator('.cov__missbtn').click();
  const dlg = page.locator('[data-missing-modal]');
  await expect(dlg).toBeVisible();
  await expect(dlg.locator('[data-modal-title]')).toContainText('注音');
  expect(await dlg.locator('.cov__miss').count()).toBeGreaterThan(10);
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
  const yong = await countOf();
  await page.getByTestId('chars-input').fill('永͸'); // 加 U+0378(未指派)后只会更少
  await expect.poll(countOf).toBeLessThanOrEqual(yong);
  await page.getByTestId('chars-input').fill('\u{40000}'); // 第 4 平面,任何字体都不会编码
  await expect.poll(countOf).toBe(0);
  await expect(page.getByTestId('catalogue-island')).toContainText('没有符合条件的字体');
});

test('glyph sheets lay out three per row on a wide screen', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('zh/fonts/wqy-bitmap-song/');
  // 岛屿是 client:visible，先把网格滚进视口再等图元出现
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const sheets = grid.locator('.gg__sheets .gg__sheet');
  await expect(sheets.nth(5)).toBeAttached();
  const boxes = await sheets.evaluateAll((els) =>
    els.slice(0, 6).map((e) => {
      const r = e.getBoundingClientRect();
      return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width) };
    }),
  );
  expect(boxes.length).toBeGreaterThanOrEqual(6);
  // 前三个同一行，第四个换行
  expect(new Set(boxes.slice(0, 3).map((b) => b.y)).size).toBe(1);
  expect(boxes[3]!.y).toBeGreaterThan(boxes[0]!.y);
  // 三列等宽，且铺满容器
  expect(new Set(boxes.slice(0, 3).map((b) => b.w)).size).toBe(1);
  const container = await grid
    .locator('.gg__sheets')
    .first()
    .evaluate((e) => Math.round(e.getBoundingClientRect().width));
  const spanned = boxes[2]!.x + boxes[2]!.w - boxes[0]!.x;
  expect(spanned).toBe(container);
});

test('jump-to-block dropdown lists covered Unicode blocks after the ranges', async ({
  page,
}) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const select = grid.getByTestId('range-select');

  // block 选项在所有分块 range 之后，且归在一个分组里
  const groups = select.locator('optgroup');
  await expect(groups).toHaveCount(1);
  const values = await select.locator('option').evaluateAll((os) =>
    os.map((o) => (o as HTMLOptionElement).value),
  );
  const firstBlock = values.findIndex((v) => v.startsWith('b:'));
  expect(firstBlock).toBeGreaterThan(0);
  expect(values.slice(0, firstBlock).every((v) => v.startsWith('r:'))).toBe(true);
  expect(values.slice(firstBlock).every((v) => v.startsWith('b:'))).toBe(true);

  // 选中某个 block 后，只显示该 block 所在的码位范围
  await select.selectOption('b:Hiragana');
  await page.waitForTimeout(400);
  // 平假名 U+3040–U+309F：只出这一页，不能因按 256 对齐而带出邻居 block
  expect(await grid.locator('.gg__sheet figcaption').allInnerTexts()).toEqual([
    'U+3040',
  ]);
  await select.selectOption('b:Katakana');
  await page.waitForTimeout(400);
  expect(await grid.locator('.gg__sheet figcaption').allInnerTexts()).toEqual([
    'U+30A0',
  ]);
});

test('a block spanning several chunk files still renders glyphs', async ({
  page,
}) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  // CJK 统一汉字横跨多个分块文件，每张 sheet 要各自找到对应分块
  await grid.getByTestId('range-select').selectOption('b:CJK Unified Ideographs');
  await page.waitForTimeout(1500);
  const painted = await grid.locator('.gg__sheet canvas').evaluateAll((cs) => {
    let n = 0;
    for (const c of cs.slice(0, 8)) {
      const d = (c as HTMLCanvasElement)
        .getContext('2d')!
        .getImageData(0, 0, (c as HTMLCanvasElement).width, 4).data;
      if (d.some((v, i) => i % 4 === 3 && v)) n++;
    }
    return n;
  });
  expect(painted).toBeGreaterThan(0);
});

test('jump-to-block has a search box that narrows the options', async ({
  page,
}) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const select = grid.getByTestId('range-select');
  const search = grid.getByTestId('range-search');
  const count = () => select.locator('option').count();
  // 岛屿是 client:visible，先等选项渲染出来再取基线
  await expect.poll(count).toBeGreaterThan(1);
  const all = await count();

  // 按名字搜
  await search.fill('hira');
  await expect.poll(count).toBeLessThan(all);
  const names = await select.locator('optgroup option').allInnerTexts();
  expect(names.some((n) => n.startsWith('Hiragana'))).toBe(true);
  expect(names.every((n) => /hira/i.test(n))).toBe(true);

  // 按码位搜
  await search.fill('4e00');
  await expect
    .poll(async () => await select.locator('optgroup option').allInnerTexts())
    .toEqual(expect.arrayContaining([expect.stringContaining('U+4E00')]));

  // 清空即还原
  await search.fill('');
  await expect.poll(count).toBe(all);
});

test('the current selection survives filtering', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const select = grid.getByTestId('range-select');
  await select.selectOption('b:Hiragana');
  // 搜一个匹配不到当前选中项的词，下拉不能变成空白
  await grid.getByTestId('range-search').fill('cyrillic');
  await expect(select).toHaveValue('b:Hiragana');
  expect(await select.locator('option').count()).toBeGreaterThan(0);
});

test('missing glyphs are boxed and titled with their code point', async ({
  page,
}) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  // 点开第一个「缺 N 字」，内容在弹窗里
  const btn = page.locator('.cov__missbtn').first();
  await btn.scrollIntoViewIfNeeded();
  await btn.click();
  const box = page.locator('[data-missing-modal]');
  await expect(box).toBeVisible();
  const chars = box.locator('.cov__miss');
  const n = await chars.count();
  expect(n).toBeGreaterThan(0);

  // 每个缺字都带 U+XXXX 的 title，且与字符本身一致
  for (const el of (await chars.all()).slice(0, 12)) {
    const ch = (await el.innerText()).trim();
    const title = await el.getAttribute('title');
    expect(title).toMatch(/^U\+[0-9A-F]{4,6}$/);
    expect(title).toBe(
      'U+' +
        ch.codePointAt(0)!.toString(16).toUpperCase().padStart(4, '0'),
    );
  }
  // 淡边框
  await expect(chars.first()).toHaveCSS('border-top-width', '1px');
});

test('missing chars open in a modal that closes again', async ({ page }) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const dlg = page.locator('[data-missing-modal]');
  await expect(dlg).toBeHidden();

  const btn = page.locator('.cov__missbtn').first();
  await btn.scrollIntoViewIfNeeded();
  const label = (await btn.innerText()).trim();
  await btn.click();
  await expect(dlg).toBeVisible();
  // 标题带上字表名与缺字数
  await expect(dlg.locator('[data-modal-title]')).toContainText(label);
  await expect(dlg.locator('.cov__miss').first()).toBeVisible();

  await dlg.locator('[data-modal-close]').click();
  await expect(dlg).toBeHidden();

  // Esc 也能关（原生 dialog 的行为）
  await btn.click();
  await expect(dlg).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(dlg).toBeHidden();
});

test('coverage section has its own variant picker, synced with the top one', async ({
  page,
}) => {
  await page.goto('zh/fonts/wqy-bitmap-song/');
  const pick = page.getByTestId('coverage-variant');
  const top = page.getByTestId('variant-select');
  await pick.scrollIntoViewIfNeeded();

  const ids = await pick.locator('option').evaluateAll((os) =>
    os.map((o) => (o as HTMLOptionElement).value),
  );
  expect(ids.length).toBeGreaterThan(1);

  // 在覆盖率这里换变体：面板跟着换，顶部下拉也跟着走
  await pick.selectOption(ids[2]!);
  await expect(top).toHaveValue(ids[2]!);
  await expect(
    page.locator(`[data-variant-panel~="${ids[2]}"]`).first(),
  ).toBeVisible();

  // 反向：在顶部换，覆盖率这边的下拉同步
  await top.selectOption(ids[0]!);
  await expect(pick).toHaveValue(ids[0]!);
});
