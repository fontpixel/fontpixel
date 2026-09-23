/** Resolve fragments without treating the ID as a CSS selector. */
export function fragmentTarget(): HTMLElement | null {
  try {
    return document.getElementById(decodeURIComponent(location.hash.slice(1)));
  } catch {
    return null;
  }
}

/** Make deep links into collapsed content visible before positioning them.
 *  A page opened at a fragment lands there at once; a jump within the page
 *  (`auto`) glides, following the root's CSS `scroll-behavior`. */
export function revealFragment(behavior: ScrollBehavior = 'instant'): void {
  const target = fragmentTarget();
  if (!target) return;
  for (let el: HTMLElement | null = target; el; el = el.parentElement) {
    if (el instanceof HTMLDetailsElement) el.open = true;
    if (el.dataset.tabValue) {
      el.closest('[data-tabs]')?.dispatchEvent(
        new CustomEvent('opf-tab', { detail: el.dataset.tabValue }),
      );
    }
  }
  requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior }));
}
