import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';

const detail = (slug: string) => JSON.parse(readFileSync(`public/data/details/${slug}.json`, 'utf8'));
const overlapKeys = [
  'tw-sc', 'jp-tw', 'jp-sc', 'kr-tw', 'kr-sc',
  'tw-sc-jp', 'tw-sc-kr', 'tw-sc-jp-kr',
  'tw-sc-union', 'tw-sc-jp-union', 'tw-sc-kr-union', 'union',
  'tw-only', 'sc-only', 'jp-only', 'kr-only',
];
const mainland: Record<string, string> = {
  en: 'Mainland China · General Simplified Han',
  zh: '中国大陆 · 通用简体字',
  'zh-Hant': '中國大陸 · 通用簡體字',
  ja: '中国本土 · 通用簡体字',
  ko: '중국 본토 · 통용 간체자',
  fr: 'Chine continentale · Han simplifiés d’usage général',
};

for (const lang of ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr']) {
  test(`CJK map has exact counts and sits between the coverage tables (${lang})`, async ({ page }) => {
    await page.goto(`${lang}/fonts/dotgothic16/`);
    const map = page.getByTestId('cjk-coverage').filter({ visible: true });
    await expect(map).toHaveCount(1);
    expect(await map.evaluate(el => ({
      previous: el.previousElementSibling?.querySelector('[data-charset="latin-basic"]') !== null,
      next: el.nextElementSibling?.querySelector('[data-charset="combined"]') !== null,
      standards: el.nextElementSibling?.nextElementSibling?.querySelector('[data-charset="gb2312"]') !== null,
    }))).toEqual({ previous: true, next: true, standards: true });
    const variant = await page.getByTestId('coverage-variant').inputValue();
    const stats = detail('dotgothic16').cjkCoverage[variant];
    expect(stats.jp[1]).toBe(2965);
    const nf = new Intl.NumberFormat(lang);
    await expect(map.locator('.cjk__heading p')).toHaveCount(0);
    await expect(map.locator('[data-cjk="han"]')).not.toContainText('%');
    await expect(map.locator('[data-cjk="combined"] strong')).toHaveText(
      stats.combined.map((n: number) => nf.format(n)).join(' / '),
    );
    await expect(map.locator('[data-cjk="combined"] .cjk__percent')).toHaveText(
      `${nf.format(Math.round(stats.combined[0] / stats.combined[1] * 1000) / 10)}%`,
    );
    await expect(map.locator('[data-cjk="sc"] .cjk__svg-label')).toHaveText(mainland[lang]!);
    await expect(map.locator('[data-cjk="jp"] .cjk__svg-label')).toContainText('JIS X 0208');
    const hierarchy = await map.evaluate(el => ({
      han: parseFloat(getComputedStyle(el.querySelector('[data-cjk="han"] .mono')!).fontSize),
      combined: parseFloat(getComputedStyle(el.querySelector('[data-cjk="combined"] strong')!).fontSize),
    }));
    expect(hierarchy.combined).toBeGreaterThan(hierarchy.han);
    await map.locator('summary').click();
    await expect(map.locator('.cjk__details')).toHaveCSS('border-left-width', '1px');
    await expect(map.locator('.cjk__details p').first()).toHaveCSS('max-width', 'none');
    await expect(map.locator('summary')).toHaveCSS('border-bottom-width', '1px');
    await expect(map.locator('.cjk__tables table')).toHaveCount(1);
    expect(await map.locator('[data-cjk-detail]').evaluateAll(rows => rows.map(row => row.getAttribute('data-cjk-detail')))).toEqual(overlapKeys);
    for (const key of overlapKeys) {
      const [have, total] = stats[key] as number[];
      const cell = map.locator(`[data-cjk-detail="${key}"] td`);
      await expect(cell.locator('span')).toHaveText(`${nf.format(have!)} / ${nf.format(total!)}`);
      await expect(cell.locator('meter')).toHaveAttribute('value', String(have));
      await expect(cell.locator('meter')).toHaveAttribute('max', String(total));
    }
    const panel = page.locator('[data-variant-panel]:visible').filter({ has: map });
    const tableCounts = async (selector: string) => (await panel.locator(selector).textContent())!.replace(/[^0-9/]/g, '');
    await expect(panel.locator('.cov__row-note')).toHaveCount(0);
    // Every figure in the map has a subsequent numeric row. Overlaps remain
    // in the map disclosure; totals and script subsets live in regular tables.
    for (const [key, chart] of [
      ['han', 'han'], ['combined', 'combined'], ['tw', 'tw'], ['sc', 'tongyong-guifan'],
      ['jp', 'jisx0208-l1'], ['kr', 'kr'], ['kr-compat', 'kr-compat'],
      ['kana', 'kana'], ['hiragana', 'hiragana'], ['katakana', 'katakana'],
      ['kana-halfwidth', 'halfwidth-kana'], ['kana-marks', 'kana-marks'], ['kana-ext', 'kana-ext'],
      ['hangul', 'hangul-syllables'], ['hangul-common', 'ksx1001-hangul'],
      ['jamo', 'jamo'], ['jamo-ext', 'jamo-ext'], ['bopomofo', 'bopomofo'],
    ]) {
      expect(await tableCounts(`[data-charset="${chart}"] td:first-of-type`)).toBe(stats[key!].join('/'));
      expect(await panel.locator(`[data-charset="${chart}"]`).evaluate(el =>
        Boolean(el.compareDocumentPosition(el.closest('[data-variant-panel]')!.querySelector('[data-testid="cjk-coverage"]')!) & Node.DOCUMENT_POSITION_PRECEDING),
      )).toBe(true);
    }
  });
}

test('CJK map follows both variant selectors', async ({ page }) => {
  await page.goto('en/fonts/wqy-bitmap-song/');
  const data = detail('wqy-bitmap-song');
  const pick = page.getByTestId('coverage-variant');
  const ids = await pick.locator('option').evaluateAll(options => options.map(o => (o as HTMLOptionElement).value));
  for (const id of [ids.at(-1)!, ids[0]!]) {
    await pick.selectOption(id);
    const map = page.getByTestId('cjk-coverage').filter({ visible: true });
    await expect(map).toHaveCount(1);
    await expect(map.locator('[data-cjk="combined"] strong')).toHaveText(
      data.cjkCoverage[id].combined.map((n: number) => n.toLocaleString('en')).join(' / '),
    );
    await expect(page.getByTestId('variant-select')).toHaveValue(id);
  }
  await page.getByTestId('variant-select').selectOption(ids[1]!);
  await expect(pick).toHaveValue(ids[1]!);
  await expect(page.getByTestId('cjk-coverage').filter({ visible: true }).locator('[data-cjk="combined"] strong')).toHaveText(
    data.cjkCoverage[ids[1]!].combined.map((n: number) => n.toLocaleString('en')).join(' / '),
  );
});

test('CJK map remains readable on a narrow dark page, including zero coverage', async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 800 });
  await page.goto('en/fonts/press-start-2p/');
  await page.evaluate(() => document.documentElement.dataset.theme = 'dark');
  const map = page.getByTestId('cjk-coverage').filter({ visible: true });
  await map.scrollIntoViewIfNeeded();
  await expect(map.locator('svg')).toBeHidden();
  await expect(map.locator('.cjk__mobile')).toBeVisible();
  await expect(map.locator('[data-cjk="han"] .mono')).toHaveText('0 / 101,996');
  await expect(map.locator('[data-cjk="combined"] strong')).toHaveText('0 / 26,727');
  await expect(map.locator('[data-cjk="combined"] .cjk__percent')).toHaveText('0%');
  await map.locator('summary').click();
  expect(await map.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test('coverage tables put totals before indented subsets and keep missing glyphs usable', async ({ page }) => {
  await page.goto('zh/fonts/dotgothic16/');
  const panel = page.locator('[data-variant-panel]:visible').filter({ has: page.getByTestId('cjk-coverage') });
  const groups = {
    gb2312: ['gb2312-l1', 'gb2312-l2'],
    'tongyong-guifan': ['tongyong-guifan-l1', 'tongyong-guifan-l2', 'tongyong-guifan-l3'],
    'changyong-3500': ['changyong-2500', 'cichangyong-1000'],
    big5: ['big5-changyong', 'big5-cichangyong'],
    tw: ['tw-changyong-4808', 'tw-cichangyong-6343'],
    joyo: ['kyoiku'],
    kana: ['hiragana', 'katakana', 'kana-marks', 'kana-ext', 'halfwidth-kana'],
    'hangul-syllables': ['ksx1001-hangul'],
    'ksx1001-hanja': ['kr', 'kr-compat'],
    jamo: ['hangul-compat-jamo', 'hangul-jamo', 'jamo-ext'],
    'gb18030-2022-l3': ['gb18030-2022-l2'],
    'gb18030-2022-l2': ['gb18030-2022-l1'],
  };
  await expect(panel.locator('[data-charset="hiragana"] th')).toHaveText('平假名');
  await expect(panel.locator('[data-charset="katakana"] th')).toHaveText('片假名');
  await expect(panel.locator('[data-charset="kana"] td').first()).toContainText('/ 579');
  await expect(panel.locator('[data-charset="jamo"] td').first()).toContainText('/ 451');
  for (const [parent, children] of Object.entries(groups)) {
    const root = panel.locator(`[data-charset="${parent}"]`);
    for (const [i, child] of children.entries()) {
      const row = panel.locator(`[data-charset="${child}"]`);
      await expect(row).toHaveAttribute('data-coverage-parent', parent);
      expect(await root.evaluate((el, steps) => {
        for (let n = 0; n < steps; n++) el = el.nextElementSibling!;
        return el.getAttribute('data-charset');
      }, i + 1)).toBe(child);
      const indent = (el: Element) => parseFloat(getComputedStyle(el.querySelector('th')!).paddingLeft);
      expect(await row.evaluate(indent)).toBeGreaterThan(await root.evaluate(indent));
      const referenceColor = await panel.locator('.cov__overview .cov__sub th').first().evaluate(el => getComputedStyle(el).color);
      expect(await row.locator('th').evaluate(el => getComputedStyle(el).color)).toBe(referenceColor);
    }
  }
  await panel.locator('[data-charset="kana-ext"] [data-missing]').click();
  const modal = page.locator('[data-missing-modal]');
  await expect(modal).toBeVisible();
  const variant = await page.getByTestId('coverage-variant').inputValue();
  await expect(modal.locator('.cov__miss')).toHaveCount(detail('dotgothic16').missingChars[variant]['kana-ext'].length > 0
    ? [...detail('dotgothic16').missingChars[variant]['kana-ext']].length : 0);
  await modal.locator('[data-modal-close]').click();
  await page.setViewportSize({ width: 320, height: 800 });
  for (const id of ['kana', 'hiragana', 'jamo']) {
    const row = panel.locator(`[data-charset="${id}"]`);
    const layout = await row.evaluate(el => {
      const th = el.querySelector('th')!;
      const scroller = el.closest('.cov__scroll')!;
      return {
        height: th.getBoundingClientRect().height,
        lineHeight: parseFloat(getComputedStyle(th).lineHeight),
        scrollable: scroller.scrollWidth > scroller.clientWidth,
        right: scroller.getBoundingClientRect().right,
      };
    });
    expect(layout.height).toBeLessThan(layout.lineHeight * 3);
    expect(layout.scrollable).toBe(true);
    expect(layout.right).toBeLessThanOrEqual(320);
  }
});

test('localized names and imported font metadata/downloads are available', async ({ page, request }) => {
  await page.goto('zh/fonts/dotgothic16/');
  await expect(page.locator('h1')).toHaveText('DotGothic点黑16');
  await page.goto('ja/fonts/dotgothic16/');
  await expect(page.locator('h1')).toHaveText('DotGothicドットゴシック16');
  await page.goto('zh/fonts/shanweizhouhei-16/');
  await expect(page.locator('h1')).toHaveText('扇尾胄黑16');
  const imported = detail('shanweizhouhei-16');
  expect(imported.meta.forms).toEqual(detail('fashionbitmap16').meta.forms);
  expect(imported.meta.searchText).toContain('扇尾胄黑');
  expect(detail('bestten').meta.searchText).toContain('10×10');
  for (const download of imported.downloads) {
    const response = await request.get(`downloads/${download.file}`);
    expect(response.ok()).toBe(true);
    const expected = readFileSync(`public/downloads/${download.file}`);
    expect(expected.length).toBe(download.bytes);
    // Preview can mark .gz assets with Content-Encoding; Playwright then
    // returns the decompressed body. Compare actual contents in either form.
    const received = await response.body();
    expect(received.equals(expected) || (
      download.file.endsWith('.gz') && received.equals(gunzipSync(expected))
    )).toBe(true);
  }
});
