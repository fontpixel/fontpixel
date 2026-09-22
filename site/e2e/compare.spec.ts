import { expect, test } from '@playwright/test';

test('compare draws a column per font and carries the type-test controls', async ({ page }) => {
  const defaults = ['press-start-2p', 'pixelify-sans'];
  await page.goto('zh/compare/');
  const cmp = page.getByTestId('compare');
  await expect(cmp.locator('canvas')).toHaveCount(2);
  for (const [i, slug] of defaults.entries()) {
    await expect(cmp.locator(`[name="compare-font-${i + 1}"]`)).toHaveValue(slug!);
  }

  // Every frame button must keep its accessible label, including icon options.
  // The Invert one once rendered blank
  // for months because its i18n key was deleted with the catalogue control that
  // used to share it, and nothing failed.
  const radios = cmp.getByTestId('frame-radios');
  for (const label of ['无', '反色', '老游戏', '高亮代码']) {
    await expect(radios.getByRole('button', { name: label, exact: true })).toBeEnabled();
  }

  // A preset fills the shared text box, and box drawing forces wrapping off
  await cmp.getByRole('button', { name: '制表符' }).click();
  await expect(cmp.locator('textarea')).toHaveValue(/┌─┬─┐/);
  await expect(cmp.getByLabel('不换行')).toBeChecked();
});

test('comparisons can exceed four fonts and keep every selection on reload', async ({ page }) => {
  await page.goto('en/compare/');
  const cmp = page.getByTestId('compare');
  const pickers = cmp.locator('select[name^="compare-font-"]');
  for (let i = 0; i < 5; i++) await cmp.getByTestId('compare-add').click();
  await expect(pickers).toHaveCount(7);
  await expect(cmp.getByTestId('compare-add')).toBeEnabled();
  await expect.poll(() => new URL(page.url()).searchParams.get('v')?.split(',').length).toBe(7);
  const selected = await pickers.evaluateAll(elements => elements.map(el => (el as HTMLSelectElement).value));
  await page.reload();
  await expect(pickers).toHaveCount(7);
  expect(await pickers.evaluateAll(elements => elements.map(el => (el as HTMLSelectElement).value))).toEqual(selected);
  await cmp.locator('textarea').fill('ABC');
  await expect.poll(() => cmp.locator('canvas').evaluateAll(elements => elements.every(canvas => {
    const data = canvas.getContext('2d')?.getImageData(0, 0, canvas.width, canvas.height).data;
    return data && data.some((value, i) => i % 4 === 3 && value > 0);
  }))).toBe(true);
  await cmp.getByRole('button', { name: 'Remove', exact: true }).nth(2).click();
  await expect(pickers).toHaveCount(6);
  expect(await pickers.evaluateAll(elements => elements.map(el => (el as HTMLSelectElement).value)))
    .toEqual(selected.filter((_, i) => i !== 2));
  await expect.poll(() => new URL(page.url()).searchParams.get('v')?.split(',').length).toBe(6);
  await page.setViewportSize({ width: 320, height: 800 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(320);
});

test('compare reports missing characters per column', async ({ page }) => {
  await page.goto('zh/compare/?v=wqy-bitmap-song:wqy-bitmap-song-12px');
  const cmp = page.getByTestId('compare');
  // ௵ (Tamil number sign) is in no font here
  await cmp.locator('textarea').fill('永A௵');
  await expect(cmp.getByTestId('missing-count').first()).toContainText('1');
});
