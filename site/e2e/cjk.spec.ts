import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';

const detail = (slug: string) => JSON.parse(readFileSync(`public/data/details/${slug}.json`, 'utf8'));
const mainland: Record<string, string> = {
  en: 'Mainland China · Standard Simplified Han',
  zh: '中国大陆 · 通用简体汉字',
  'zh-Hant': '中國大陸 · 通用簡體漢字',
  ja: '中国本土 · 標準簡体字',
  ko: '중국 본토 · 표준 간체 한자',
  fr: 'Chine continentale · Han simplifiés normalisés',
};

for (const lang of ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr']) {
  test(`CJK map has exact counts and sits between the coverage tables (${lang})`, async ({ page }) => {
    await page.goto(`${lang}/fonts/dotgothic16/`);
    const map = page.getByTestId('cjk-coverage').filter({ visible: true });
    await expect(map).toHaveCount(1);
    expect(await map.evaluate(el => ({
      previous: el.previousElementSibling?.querySelector('[data-charset="latin-basic"]') !== null,
      next: el.nextElementSibling?.querySelector('[data-charset="gb2312"]') !== null,
    }))).toEqual({ previous: true, next: true });
    const variant = await page.getByTestId('coverage-variant').inputValue();
    const stats = detail('dotgothic16').cjkCoverage[variant];
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
    const hierarchy = await map.evaluate(el => ({
      han: parseFloat(getComputedStyle(el.querySelector('[data-cjk="han"] .mono')!).fontSize),
      combined: parseFloat(getComputedStyle(el.querySelector('[data-cjk="combined"] strong')!).fontSize),
    }));
    expect(hierarchy.combined).toBeGreaterThan(hierarchy.han);
    await map.locator('summary').click();
    await expect(map.locator('.cjk__details')).toHaveCSS('border-left-width', '1px');
    await expect(map.locator('summary')).toHaveCSS('border-bottom-width', '1px');
    for (const [key, pair] of Object.entries(stats)) {
      const [have, total] = pair as number[];
      const cell = map.locator(`[data-cjk-detail="${key}"] td`);
      await expect(cell.locator('span')).toHaveText(`${nf.format(have!)} / ${nf.format(total!)}`);
      await expect(cell.locator('meter')).toHaveAttribute('value', String(have));
      await expect(cell.locator('meter')).toHaveAttribute('max', String(total));
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
  await expect(map.locator('[data-cjk="combined"] strong')).toHaveText('0 / 26,644');
  await expect(map.locator('[data-cjk="combined"] .cjk__percent')).toHaveText('0%');
  await map.locator('summary').click();
  expect(await map.evaluate(el => el.scrollWidth <= el.clientWidth)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
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
