import { expect, test } from '@playwright/test';
import { SAMPLES } from '../src/lib/samples';

test('catalogue presets follow typed text and preserve multiline code', async ({ page }) => {
  await page.goto('en/?q=dylex-terminal');
  const sample = page.getByTestId('sample-input');
  const preset = page.getByTestId('preset-select');
  await expect(preset).toBeEnabled();
  await expect(preset).toHaveValue('');
  await expect(preset.locator('option:checked')).toHaveText('Preset');
  await expect(preset.locator('option[value=""]')).toBeEnabled();
  const defaultPreview = page.locator('[data-slug="dylex-terminal"] .card__sample svg');
  await expect(defaultPreview).toBeVisible();
  const defaultSvg = await defaultPreview.evaluate(el => el.outerHTML);
  await preset.selectOption('zh-Hans');
  await expect(sample).toHaveValue(SAMPLES['zh-Hans']!);
  await sample.fill('Custom specimen');
  await expect(preset.locator('option:checked')).toHaveText('Preset');
  // Reset must fire even when unmatched custom text already shows "Preset".
  await preset.focus();
  await preset.press('Home');
  await expect(sample).toHaveValue('');
  await expect(defaultPreview).toBeVisible();
  expect(await defaultPreview.evaluate(el => el.outerHTML)).toBe(defaultSvg);
  await sample.fill(SAMPLES.latin!);
  await expect(preset).toHaveValue('latin');
  await preset.selectOption('');
  await expect(sample).toHaveValue('');
  await expect(preset).toHaveValue('');
  await expect(defaultPreview).toBeVisible();
  expect(await defaultPreview.evaluate(el => el.outerHTML)).toBe(defaultSvg);

  await preset.selectOption('javascript');
  await expect(sample).toHaveValue(SAMPLES.javascript!);
  await expect(page.getByRole('radio', { name: 'Highlighted code', exact: true })).toBeChecked();
  await expect(page.getByRole('combobox', { name: 'Code language' })).toHaveValue('javascript');
  const canvas = page.locator('[data-slug="dylex-terminal"] .card__sample canvas');
  await canvas.scrollIntoViewIfNeeded();
  // Verify actual keyword coloring, not just that the frame changed class.
  await expect.poll(() => canvas.evaluate((c: HTMLCanvasElement) => {
    if (!c.width || !c.height) return false;
    const pixels = c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data;
    const colors = new Set<string>();
    for (let i = 0; i < pixels.length; i += 4) colors.add(`${pixels[i]},${pixels[i + 1]},${pixels[i + 2]}`);
    return colors.has('86,156,214') && colors.has('106,153,85');
  })).toBe(true);
  await expect(page.locator('[data-slug="dylex-terminal"] .card__sample')).toHaveCSS('max-height', '192px');
});

test('catalogue frames keep SVG defaults cheap and color custom text correctly', async ({ page }) => {
  const bdfs: string[] = [];
  page.on('request', r => { if (r.url().includes('.bdf.gz')) bdfs.push(r.url()); });
  await page.goto('en/?q=dylex-terminal');
  const card = page.locator('[data-slug="dylex-terminal"]');
  const preview = card.locator('.card__sample');
  await expect(page.getByRole('radio', { name: 'Old game', exact: true })).toBeEnabled();
  await page.getByRole('radio', { name: 'Old game', exact: true }).check();
  await expect(preview.locator('svg')).toBeVisible();
  await expect(preview).toHaveCSS('background-color', 'rgb(19, 19, 83)');
  await expect(preview).toHaveCSS('color', 'rgb(240, 240, 252)');
  await page.getByRole('radio', { name: 'Invert', exact: true }).check();
  await expect(preview).toHaveCSS('filter', 'invert(1)');
  expect(bdfs).toEqual([]);

  await page.getByRole('radio', { name: 'Old game', exact: true }).check();
  await page.getByTestId('sample-input').fill('ABC');
  const canvas = preview.locator('canvas');
  await expect.poll(() => canvas.evaluate((c: HTMLCanvasElement) => c.width)).toBeGreaterThan(0);
  const colors = await canvas.evaluate((c: HTMLCanvasElement) => {
    const pixels = c.getContext('2d')!.getImageData(0, 0, c.width, c.height).data;
    const found = new Set<string>();
    for (let i = 0; i < pixels.length; i += 4) found.add(`${pixels[i]},${pixels[i + 1]},${pixels[i + 2]}`);
    return [...found];
  });
  expect(colors).toContain('240,240,252');
  expect(colors).toContain('19,19,83');
});

test('preview frame and code language survive catalogue pagination', async ({ page }) => {
  await page.goto('en/');
  await expect(page.getByTestId('preset-select')).toBeEnabled();
  await page.getByTestId('preset-select').selectOption('javascript');
  await page.getByRole('combobox', { name: 'Code language' }).selectOption('typescript');
  await page.getByTestId('page-next').first().click();
  await expect(page.getByTestId('preset-select')).toHaveValue('javascript');
  await expect(page.getByTestId('sample-input')).toHaveValue(SAMPLES.javascript!);
  await expect(page.getByRole('radio', { name: 'Highlighted code', exact: true })).toBeChecked();
  await expect(page.getByRole('combobox', { name: 'Code language' })).toHaveValue('typescript');
});

for (const path of ['zh/', 'zh/compare/', 'zh/fonts/dylex-terminal/']) {
  test(`icon controls are labelled, keyboard accessible and fit at 300px: ${path}`, async ({ page }) => {
    await page.setViewportSize({ width: 300, height: 900 });
    await page.goto(path);
    const radios = page.getByTestId('frame-radios');
    await expect(radios.getByRole('radio', { name: '老游戏', exact: true })).toBeEnabled();
    await expect(radios.locator('label[title="老游戏"] svg')).toBeVisible();
    await expect(radios.locator('label[title="高亮代码"] svg')).toBeVisible();
    await expect(radios.getByText('老游戏', { exact: true })).toHaveCount(0);
    const game = radios.getByRole('radio', { name: '老游戏', exact: true });
    await game.check();
    await game.press('ArrowRight');
    await expect(radios.getByRole('radio', { name: '高亮代码', exact: true })).toBeChecked();
    await expect(radios.getByRole('combobox', { name: '代码语言' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}
