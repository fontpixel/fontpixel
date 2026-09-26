import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { writeFile } from 'node:fs/promises';

const paths = ['en/', 'zh/', 'en/page/2/', 'en/fonts/galmuri/', 'en/compare/',
  'en/about/', 'en/tools/', 'en/bdfparser_js/', 'en/bdfparser_js/api/types/headers/', '404'];

for (const mode of ['desktop-light', 'mobile-dark'] as const) {
  for (const path of paths) {
    test(`axe ${mode}: ${path}`, async ({ page }, testInfo) => {
      test.setTimeout(120_000);
      await page.setViewportSize(mode === 'mobile-dark' ? { width: 390, height: 844 } : { width: 1365, height: 900 });
      await page.addInitScript((theme) => localStorage.setItem('opf-theme', theme), mode.endsWith('dark') ? 'dark' : 'light');
      await page.goto(path);
      await expect(page.locator('astro-island[client="load"][ssr]')).toHaveCount(0);
      const results = await new AxeBuilder({ page }).analyze();
      const report = testInfo.outputPath('axe.json');
      await writeFile(report, JSON.stringify(results, null, 2));
      await testInfo.attach('axe-results', { path: report, contentType: 'application/json' });
      expect(results.violations.map(({ id, nodes }) => ({ id, nodes: nodes.map(n => ({ target: n.target, summary: n.failureSummary })) }))).toEqual([]);
    });
  }
}

test('skip link transfers keyboard focus to main and keeps a visible focus ring', async ({ page }) => {
  await page.goto('en/about/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused();
  const outline = await page.locator(':focus').evaluate(el => getComputedStyle(el).outlineStyle);
  expect(outline).not.toBe('none');
  await page.keyboard.press('Enter');
  await expect(page.locator('main')).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(page.locator('.about__intro a')).toBeFocused();
});

test('doc tabs support arrows, Home/End, and a single Tab stop', async ({ page }) => {
  await page.goto('en/bdfparser_js/');
  const group = page.locator('[data-tabs]').first();
  const tabs = group.getByRole('tab');
  await tabs.first().focus();
  await page.keyboard.press('ArrowRight');
  await expect(tabs.nth(1)).toBeFocused();
  await expect(tabs.nth(1)).toHaveAttribute('aria-selected', 'true');
  await expect(group.getByRole('tabpanel')).toHaveCount(1);
  await page.keyboard.press('End');
  await expect(tabs.last()).toBeFocused();
  await page.keyboard.press('Home');
  await expect(tabs.first()).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(group.getByRole('tabpanel')).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(tabs.first()).toBeFocused();
});

test('glyph sheets can be inspected and dismissed entirely by keyboard', async ({ page }) => {
  await page.goto('en/fonts/wqy-bitmap-song/');
  const grid = page.getByTestId('glyph-grid');
  await grid.scrollIntoViewIfNeeded();
  const sheet = grid.locator('.gg__sheet canvas').first();
  await expect(sheet).toHaveAttribute('data-cell', /\d+/);
  await sheet.focus();
  const initial = await sheet.getAttribute('aria-label');
  await page.keyboard.press('ArrowRight');
  await expect(sheet).not.toHaveAttribute('aria-label', initial!);
  await page.keyboard.press('Enter');
  const inspector = page.getByTestId('glyph-inspector');
  await expect(inspector).toBeVisible();
  await expect(inspector).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(inspector).toHaveCount(0);
  await expect(sheet).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(sheet).not.toBeFocused();
});

test('coverage dialog traps focus, closes on Escape, and returns it to the opener', async ({ page }) => {
  await page.goto('en/fonts/wqy-bitmap-song/');
  const opener = page.locator('[data-variant-panel]:not([hidden]) [data-charset="bopomofo"] .cov__missbtn');
  await opener.focus();
  await page.keyboard.press('Enter');
  const dialog = page.locator('[data-missing-modal]');
  await expect(dialog).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  for (const key of ['Tab', 'Shift+Tab']) {
    await page.keyboard.press(key);
    expect(await dialog.evaluate(el => el.contains(document.activeElement))).toBe(true);
  }
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(opener).toBeFocused();
});

test('header menus open with Space and Tab or Shift+Tab exits without a focus trap', async ({ page }) => {
  await page.goto('en/');
  const menu = page.getByTestId('tools-menu');
  const trigger = menu.getByRole('link', { name: 'Tools', exact: true });
  await trigger.focus();
  await trigger.press(' ');
  await expect(menu.getByRole('menuitem').first()).toBeFocused();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press('Tab');
  await expect(page.locator('.site-nav > a[href="/en/about/"]')).toBeFocused();
  await expect(trigger).toHaveAttribute('aria-expanded', 'false');
  await page.keyboard.press('Shift+Tab');
  await expect(trigger).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(page.locator('.site-nav > a[href="/en/compare/"]')).toBeFocused();
  await expect(trigger).toHaveAttribute('aria-expanded', 'false');
});
