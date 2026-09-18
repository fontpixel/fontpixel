/** Resolve fragments without treating the ID as a CSS selector. */
export function fragmentTarget(): HTMLElement | null {
  try {
    return document.getElementById(decodeURIComponent(location.hash.slice(1)));
  } catch {
    return null;
  }
}

/** Make deep links into collapsed content visible before positioning them. */
export function revealFragment(): void {
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
  requestAnimationFrame(() => target.scrollIntoView({ block: 'start' }));
}
