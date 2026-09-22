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
  await expect(page.getByRole('button', { name: 'Highlighted code', exact: true })).toHaveAttribute('aria-pressed', 'true');
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
  await expect(page.getByRole('button', { name: 'Old game', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Old game', exact: true }).click();
  await expect(preview.locator('svg')).toBeVisible();
  await expect(preview).toHaveCSS('background-color', 'rgb(19, 19, 83)');
  await expect(preview).toHaveCSS('color', 'rgb(240, 240, 252)');
  await page.getByRole('button', { name: 'Invert', exact: true }).click();
  await expect(preview).toHaveCSS('filter', 'invert(1)');
  expect(bdfs).toEqual([]);

  await page.getByRole('button', { name: 'Old game', exact: true }).click();
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
  await expect(page.getByRole('button', { name: 'Highlighted code', exact: true })).toHaveAttribute('aria-pressed', 'true');
  await expect(page.getByRole('combobox', { name: 'Code language' })).toHaveValue('typescript');
});

for (const path of ['zh/', 'zh/compare/', 'zh/fonts/dylex-terminal/']) {
  test(`icon controls are labelled, keyboard accessible and fit at 300px: ${path}`, async ({ page }) => {
    await page.setViewportSize({ width: 300, height: 900 });
    await page.goto(path);
    const radios = page.getByTestId('frame-radios');
    await expect(radios.getByRole('button', { name: '老游戏', exact: true })).toBeEnabled();
    await expect(radios.locator('button[title="老游戏"] svg')).toBeVisible();
    await expect(radios.locator('button[title="高亮代码"] svg')).toBeVisible();
    await expect(radios.getByText('老游戏', { exact: true })).toHaveCount(0);
    const game = radios.getByRole('button', { name: '老游戏', exact: true });
    await game.click();
    await expect(game).toHaveAttribute('aria-pressed', 'true');
    await radios.getByRole('button', { name: '高亮代码', exact: true }).click();
    await expect(radios.getByRole('button', { name: '高亮代码', exact: true })).toHaveAttribute('aria-pressed', 'true');
    await expect(radios.getByRole('combobox', { name: '代码语言' })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}

test('preview style buttons are all in the Tab order', async ({ page }) => {
  await page.goto('en/?q=dylex-terminal');
  const frames = page.getByTestId('frame-radios');
  const buttons = frames.getByRole('button');
  await expect(buttons).toHaveCount(4);
  await expect(buttons.first()).toBeEnabled();
  await buttons.first().focus();
  for (let i = 1; i < 4; i++) {
    await page.keyboard.press('Tab');
    await expect(buttons.nth(i)).toBeFocused();
  }
});

test('filter button groups are one Tab stop with arrow-key navigation', async ({ page }) => {
  await page.goto('en/');
  await expect(page.getByTestId('catalogue-island')).toHaveAttribute('data-ready', 'true', {
    timeout: 20_000,
  });
  for (const sectionId of [
    'filter-scripts',
    'filter-sizes',
    'filter-form',
    'filter-spacing-weight',
    'filter-license',
  ]) {
    const toolbar = page.locator(`#${sectionId} [role="toolbar"]`);
    const buttons = toolbar.getByRole('button');
    const count = await buttons.count();
    expect(count).toBeGreaterThan(1);
    expect(await buttons.evaluateAll((items) =>
      items.filter((item) => (item as HTMLButtonElement).tabIndex === 0).length,
    )).toBe(1);

    const current = toolbar.locator('button[tabindex="0"]');
    const currentIndex = await current.evaluate((item) =>
      [...item.parentElement!.querySelectorAll('button')].indexOf(item as HTMLButtonElement),
    );
    await current.focus();
    await page.keyboard.press('ArrowDown');
    await expect(buttons.nth((currentIndex + 1) % count)).toBeFocused();
    await page.keyboard.press('Tab');
    expect(await toolbar.evaluate((element) => element.contains(document.activeElement))).toBe(false);
  }
});
