import { expect, test } from '@playwright/test';

const PAGES = [
  'zh/',
  'en/',
  'zh/about/',
  'zh/fonts/wqy-bitmap-song/',
  // 变体最多、标签最长的两个家族：尺寸表与变体下拉最容易撑破窄屏
  'zh/fonts/misc-fixed/',
  'en/fonts/ark-pixel/',
];
// 300px 是实际在售最窄的手机（如 Galaxy Fold 外屏）的可视宽度
const WIDTHS = [1440, 900, 700, 480, 360, 300];

// 页面永远不该出现横向滚动条：过宽的内容（覆盖率表格、像素站名）应各自
// 在容器内缩放或滚动，而不是把整页撑破。
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
      expect(worst.scrollWidth, `最宽越界元素：${worst.who}`).toBeLessThanOrEqual(
        worst.clientWidth,
      );
    });
  }
}
