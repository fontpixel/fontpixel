import { expect, test, type Locator, type Page } from '@playwright/test';

async function longPress(page: Page, target: Locator) {
  const box = (await target.boundingBox())!;
  const at = { clientX: box.x + box.width / 2, clientY: box.y + box.height / 2 };
  await target.dispatchEvent('pointerdown', { pointerType: 'touch', isPrimary: true, bubbles: true, ...at });
  await page.waitForTimeout(650);
  await target.dispatchEvent('pointerup', { pointerType: 'touch', isPrimary: true, bubbles: true, ...at });
}

test.describe('titles on touch screens', () => {
  test.use({ hasTouch: true, isMobile: true, viewport: { width: 390, height: 800 } });

  test('a long press shows a title and does not follow the link', async ({ page }) => {
    await page.goto('en/fonts/misc-fixed/');
    const link = page.locator('[data-script="zh-hans"] a');
    const rule = await link.getAttribute('title');
    expect(rule).toBeTruthy();
    await link.scrollIntoViewIfNeeded();
    await longPress(page, link);
    const tip = page.locator('.touch-title');
    await expect(tip).toHaveText(rule!);
    await expect(tip).toBeInViewport();
    // The release's click is swallowed, so the page stays put.
    await link.dispatchEvent('click');
    await expect(page).toHaveURL(/\/fonts\/misc-fixed\/$/);
    // Android's long press arrives as a contextmenu event; it must not open the system menu.
    const mark = page.locator('[data-script="zh-hans"] [data-testid="variant-mark"]');
    await mark.dispatchEvent('pointerdown', { pointerType: 'touch', isPrimary: true, bubbles: true });
    await expect(tip).toHaveCount(0);
    const prevented = await mark.evaluate((el) => !el.dispatchEvent(new MouseEvent('contextmenu', { bubbles: true, cancelable: true })));
    expect(prevented).toBe(true);
    await expect(tip).toHaveText((await mark.getAttribute('title'))!);
    // A quick tap is still a tap.
    await page.locator('body').dispatchEvent('pointerdown', { pointerType: 'touch', isPrimary: true, bubbles: true });
    await expect(tip).toHaveCount(0);
  });

  test('a short tap does not show a title', async ({ page }) => {
    await page.goto('en/fonts/misc-fixed/');
    const mark = page.locator('[data-script="latin"] [data-testid="variant-mark"]');
    await mark.dispatchEvent('pointerdown', { pointerType: 'touch', isPrimary: true, bubbles: true });
    await mark.dispatchEvent('pointerup', { pointerType: 'touch', isPrimary: true, bubbles: true });
    await page.waitForTimeout(650);
    await expect(page.locator('.touch-title')).toHaveCount(0);
  });
});
