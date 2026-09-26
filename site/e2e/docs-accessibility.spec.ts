import { readdirSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';

const docs = readdirSync(new URL('../src/content/docs/', import.meta.url), { recursive: true })
  .filter((p): p is string => typeof p === 'string' && /\.(md|mdx)$/.test(p))
  .map(p => 'en/' + p.replace(/\.(md|mdx)$/, '').replace(/\bindex$/, '').replace(/\/?$/, '/'));

for (const path of docs) {
  test(`documentation accessibility: ${path}`, async ({ page }, testInfo) => {
    test.setTimeout(120_000);
    await page.goto(path);
    await expect(page.locator('astro-island[client="load"][ssr]')).toHaveCount(0);
    const results = await new AxeBuilder({ page }).analyze();
    const report = testInfo.outputPath('axe.json');
    await writeFile(report, JSON.stringify(results, null, 2));
    expect(results.violations.map(v => ({ id: v.id, nodes: v.nodes.map(n => ({ target: n.target, summary: n.failureSummary })) }))).toEqual([]);
  });
}

test('tooltips describe their trigger and Escape dismisses them without moving focus', async ({ page }) => {
  await page.goto('en/bdfparser_js/font/');
  const trigger = page.locator('.tt').first();
  await trigger.focus();
  await expect(trigger).toHaveAccessibleDescription('Tuple in TypeScript = Fixed-length Array in JavaScript');
  await expect(trigger.getByRole('tooltip')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(trigger.getByRole('tooltip')).toBeHidden();
  await expect(trigger).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(trigger).not.toBeFocused();
});
