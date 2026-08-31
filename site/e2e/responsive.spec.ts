import { expect, test } from '@playwright/test';

const PAGES = [
  'zh/',
  'en/',
  'zh/about/',
  'zh/fonts/wqy-bitmap-song/',
  // the two families with the most variants and longest labels: their size table and variant dropdown are most likely to overflow a narrow screen
  'zh/fonts/misc-fixed/',
  'en/fonts/ark-pixel/',
];
// 300px is the viewport width of the narrowest phones actually on sale (e.g. Galaxy Fold's outer screen)
const WIDTHS = [1440, 900, 700, 480, 360, 300];

// the page should never show a horizontal scrollbar: overly wide content (coverage tables,
// pixel site names) should each scale or scroll within its own container, not blow out the whole page.
for (const path of PAGES) {
  for (const width of WIDTHS) {
    test(`no horizontal overflow: ${path} @${width}px`, async ({ page }) => {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(path);
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(500);
      const worst = await page.evaluate(() => {
        const W = document.documentElement.clientWidth;
        const el = [...document.querySelectorAll('*')]
          .map((x) => ({ x, r: x.getBoundingClientRect() }))
          .filter(({ r }) => r.right > W + 1 && r.width > 0)[0];
        return {
          scrollWidth: document.documentElement.scrollWidth,
          clientWidth: W,
          who: el ? `${el.x.tagName}.${String(el.x.className).split(' ')[0]}` : '',
        };
      });
      expect(worst.scrollWidth, `widest overflowing element: ${worst.who}`).toBeLessThanOrEqual(
        worst.clientWidth,
      );
    });
  }
}
