import { expect, test } from '@playwright/test';

for (const width of [1280, 360]) {
  test(`large default specimens stay compact and scroll without loading fonts (${width}px)`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    const fontRequests: string[] = [];
    page.on('request', r => { if (r.url().includes('.bdf.gz')) fontRequests.push(r.url()); });
    await page.goto('en/?q=gossip');
    const zoom = page.getByTestId('zoom-select');
    await expect(zoom).toBeEnabled();
    for (const value of ['1', '2', '3']) {
      await zoom.selectOption(value);
      for (const slug of ['gossip', 'gossip-icons']) {
        const card = page.locator(`[data-slug="${slug}"]`);
        await card.scrollIntoViewIfNeeded();
        await expect(card.locator('.card__sample svg')).toBeVisible();
        const sizes = await card.evaluate(el => {
          const sample = el.querySelector<HTMLElement>('.card__sample')!;
          const name = el.querySelector<HTMLElement>('.card__namecanvas')!;
          const svg = el.querySelector<SVGSVGElement>('.card__sample svg')!;
          return {
            card: el.getBoundingClientRect().height,
            sample: sample.getBoundingClientRect().height,
            name: name.getBoundingClientRect().height,
            overflow: sample.scrollHeight > sample.clientHeight,
            scale: Number(svg.getAttribute('height')) / svg.viewBox.baseVal.height,
          };
        });
        expect(sizes.card).toBeLessThan(450);
        expect(sizes.sample).toBeLessThanOrEqual(192);
        expect(sizes.name).toBeLessThanOrEqual(80);
        expect(sizes.overflow).toBe(true);
        expect(sizes.scale).toBe(1);
        const sample = card.locator('.card__sample');
        await sample.hover();
        await page.mouse.wheel(0, 180);
        await expect.poll(() => sample.evaluate(el => el.scrollTop)).toBeGreaterThan(0);
        await sample.evaluate(el => el.scrollTop = 0);
      }
    }
    expect(fontRequests).toEqual([]);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  });
}

test('long custom specimens stay bounded and reflow when the viewport changes', async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.goto('en/?q=gossip');
  const card = page.locator('[data-slug="gossip"]');
  const sample = card.locator('.card__sample');
  const canvas = sample.locator('canvas');
  await expect(page.getByTestId('sample-input')).toBeEnabled();
  await page.getByTestId('sample-input').fill('Sphinx of black quartz, judge my vow. '.repeat(8));
  await sample.scrollIntoViewIfNeeded();
  await expect.poll(() => canvas.evaluate((c: HTMLCanvasElement) => c.height)).toBeGreaterThan(192);
  const before = await canvas.evaluate((c: HTMLCanvasElement) => c.width);
  await expect(card.locator('[data-testid="missing-chip"]')).toHaveCount(0);
  await page.setViewportSize({ width: 360, height: 900 });
  await sample.scrollIntoViewIfNeeded();
  await expect.poll(() => canvas.evaluate((c: HTMLCanvasElement) => c.width)).toBeLessThan(before);
  expect(await sample.evaluate(el => el.getBoundingClientRect().height)).toBeLessThanOrEqual(192);
  expect(await canvas.evaluate((c: HTMLCanvasElement) => c.getBoundingClientRect().width === c.width)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});
