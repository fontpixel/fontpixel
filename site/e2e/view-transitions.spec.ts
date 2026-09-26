import { expect, test, type Page } from '@playwright/test';

// Cross-document view transitions (src/lib/viewtransition.ts, styles/transitions.css).
// Each document records whether it was revealed with a transition still running.
// Chromium drops one silently when, e.g., a page's external stylesheets are still
// loading while an inline body script runs, so these tests also guard
// astro.config's inlineStylesheets.

async function trackReveals(page: Page): Promise<void> {
  await page.addInitScript(() => {
    addEventListener('pagereveal', (e) => {
      (window as unknown as { __vt: string }).__vt = (e as Event & { viewTransition?: unknown }).viewTransition
        ? 'yes'
        : 'no';
    });
  });
}

const revealed = (page: Page) =>
  expect.poll(() => page.evaluate(() => (window as unknown as { __vt?: string }).__vt ?? ''));

const namedElements = (page: Page) =>
  page.evaluate(() => document.querySelectorAll('[style*="view-transition-name"]').length);

test('a catalogue card grows into its font page and shrinks back into the grid', async ({ page }) => {
  await trackReveals(page);
  await page.goto('en/');
  const card = page.locator('[data-testid="catalogue-island"] .card').nth(2);
  const slug = await card.getAttribute('data-slug');
  await card.locator('a').click();
  await page.waitForURL(new RegExp(`/en/fonts/${slug}/$`));
  await revealed(page).toBe('yes');

  await page.evaluate(() => delete (window as unknown as { __vt?: string }).__vt);
  await page.goBack({ waitUntil: 'commit' });
  await page.waitForURL(/\/en\/$/);
  await revealed(page).toBe('yes');
  // The returning card is named only for the transition's duration.
  await expect.poll(() => namedElements(page)).toBe(0);
});

test('other navigations switch pages without a transition', async ({ page }) => {
  await trackReveals(page);
  await page.goto('en/fonts/galmuri/');
  await page.locator('.site-footer a[href$="/en/about/"]').click();
  await page.waitForURL(/\/en\/about\/$/);
  await revealed(page).toBe('no');
});

test('a header icon grows into the page it opens', async ({ page }) => {
  await trackReveals(page);
  await page.goto('en/fonts/galmuri/');
  for (const [name, url] of [
    ['About', /\/en\/about\/$/],
    ['Compare fonts', /\/en\/compare\/$/],
    ['Tools', /\/en\/tools\/$/],
  ] as const) {
    await page.evaluate(() => delete (window as unknown as { __vt?: string }).__vt);
    await page.locator('.site-nav').getByRole('link', { name, exact: true }).click();
    await page.waitForURL(url);
    await revealed(page).toBe('yes');
    // The stand-in sheet and the class exist only while the transition runs.
    await expect.poll(() => namedElements(page)).toBe(0);
    await expect(page.locator('html')).not.toHaveClass(/\bnav-vt\b/);
  }
});

test.describe('with reduced motion', () => {
  // Emulated per page: the reducedMotion fixture option did not reach the page here.
  test.beforeEach(async ({ page }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' });
  });

  test('opening a font page does not animate', async ({ page }) => {
    await trackReveals(page);
    await page.goto('en/');
    await page.locator('[data-testid="catalogue-island"] .card a').first().click();
    await page.waitForURL(/\/en\/fonts\//);
    await revealed(page).toBe('no');
  });

  test('the theme toggle switches at once', async ({ page }) => {
    await page.goto('en/');
    const html = page.locator('html');
    const initial = await html.getAttribute('data-theme');
    const flipped = initial === 'dark' ? 'light' : 'dark';
    await page.getByTestId('theme-toggle').click();
    await page.getByTestId('theme-menu').locator(`[data-theme-palette="red"][data-theme-mode="${flipped}"]`).click();
    // Applied synchronously in the click handler: no transition to wait for.
    expect(await html.getAttribute('data-theme')).toBe(flipped);
    await expect(html).not.toHaveClass(/theme-vt/);
  });
});
