/**
 * View Transitions: the catalogue card that grows into its font page (and
 * shrinks back into the grid on return), the header icon that grows into the
 * page it links to, plus the circular theme reveal.
 *
 * The page transition is cross-document: the site stays a multi-page app and
 * the browser snapshots the old and new documents. Only one card may carry
 * the shared names at a time (names must be unique and the grid has hundreds
 * of cards), so the clicked card is named in `pageswap` and the card being
 * returned to in `pagereveal`. A header link marked `data-vt-nav` is named
 * in `pageswap` too; the page it opens has nothing of that shape, so it adds a
 * viewport-sized stand-in for the link to grow into. Every other navigation
 * skips the transition.
 *
 * `pagereveal` fires at the first rendering opportunity, before deferred
 * module scripts are guaranteed to have run, so the installer is serialized
 * into a classic inline script in <head> by `pageTransitionScript`. Keep
 * `pageKind`, `fontSlug` and `installPageTransitions` free of imports and of
 * references to anything else in this module.
 */

export type PageKind = 'catalogue' | 'font' | 'other';

interface Config {
  base: string;
  langs: readonly string[];
}

/** Which kind of page a pathname is: the catalogue grid (any page), a font page, or neither. */
export function pageKind(pathname: string, base: string, langs: readonly string[]): PageKind {
  const b = base.replace(/\/$/, '');
  if (b && pathname !== b && !pathname.startsWith(b + '/')) return 'other';
  const p = pathname.slice(b.length);
  const l = langs.map((x) => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  if (new RegExp(`^/(?:${l})/(?:page/\\d+/?)?$`).test(p)) return 'catalogue';
  if (new RegExp(`^/(?:${l})/fonts/[^/]+/?$`).test(p)) return 'font';
  return 'other';
}

/** The slug of a font page's pathname, or null for any other page. */
export function fontSlug(pathname: string, base: string, langs: readonly string[]): string | null {
  const b = base.replace(/\/$/, '');
  if (b && !pathname.startsWith(b + '/')) return null;
  const l = langs.map((x) => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
  const m = new RegExp(`^/(?:${l})/fonts/([^/]+)/?$`).exec(pathname.slice(b.length));
  if (!m) return null;
  try {
    return decodeURIComponent(m[1]!);
  } catch {
    return null;
  }
}

/** Radius that takes a circle centred at (x, y) past the farthest viewport corner. */
export function revealRadius(x: number, y: number, width: number, height: number): number {
  return Math.ceil(Math.hypot(Math.max(x, width - x), Math.max(y, height - y)));
}

/** A circle() radius as a percentage of a w×h reference box, which CSS resolves
 *  against the box's diagonal divided by √2. */
export function revealPercent(radius: number, width: number, height: number): number {
  return (radius / (Math.hypot(width, height) / Math.SQRT2)) * 100;
}

/** The translation of a computed `transform` (`matrix(...)` or `matrix3d(...)`), or null for `none` or anything unparsable. */
export function transformOffset(transform: string): [number, number] | null {
  const m = /^matrix(3d)?\(([^)]*)\)$/.exec(transform.trim());
  if (!m) return null;
  const v = m[2]!.split(',').map(Number);
  if (v.some((n) => !Number.isFinite(n))) return null;
  if (m[1] ? v.length !== 16 : v.length !== 6) return null;
  return m[1] ? [v[12]!, v[13]!] : [v[4]!, v[5]!];
}

// The Navigation API global, missing from TypeScript's DOM lib. Type-only: emits nothing.
declare const navigation: { activation?: { from?: { url?: string } | null } | null } | undefined;

interface VT {
  ready: Promise<unknown>;
  finished: Promise<unknown>;
  skipTransition(): void;
}

/** Registers the pageswap/pagereveal handlers. Runs in the browser, serialized; see the module comment. */
export function installPageTransitions(cfg: Config): void {
  const FROM_KEY = 'opf-vt-from';
  const NAV_KEY = 'opf-vt-nav';
  const kindOf = (url: string) => pageKind(new URL(url, location.href).pathname, cfg.base, cfg.langs);
  const slugOf = (url: string) => fontSlug(new URL(url, location.href).pathname, cfg.base, cfg.langs);
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  let restored = false;
  let clicked = '';
  let navLink: HTMLAnchorElement | null = null;

  addEventListener('pageshow', (e) => {
    restored = (e as PageTransitionEvent).persisted;
  });
  // Fallback destination for browsers whose pageswap carries no NavigationActivation.
  addEventListener('click', (e) => {
    const a = (e.target as Element | null)?.closest?.('a[href]') as HTMLAnchorElement | null;
    clicked = a ? a.href : '';
    navLink = a?.closest('[data-vt-nav]') ? a : null;
  }, true);
  const noHash = (url: string) => url.split('#')[0]!;

  function nameCard(slug: string, vt: VT): boolean {
    const card = document.querySelector<HTMLElement>(`.card[data-slug="${CSS.escape(slug)}"]`);
    if (!card) return false;
    const r = card.getBoundingClientRect();
    if (r.bottom <= 0 || r.top >= innerHeight || r.width === 0) return false;
    const parts: Array<[HTMLElement | null, string]> = [
      [card, 'font-card'],
      [card.querySelector<HTMLElement>('[data-vt="name"]'), 'font-name'],
      [card.querySelector<HTMLElement>('[data-vt="preview"]'), 'font-preview'],
    ];
    for (const [el, name] of parts) if (el) el.style.viewTransitionName = name;
    // A page restored from the back/forward cache must not come back still named.
    vt.finished.finally(() => {
      for (const [el] of parts) if (el) el.style.viewTransitionName = '';
    });
    return true;
  }

  function nameNavLink(to: string, vt: VT): boolean {
    const a = navLink;
    if (!a || noHash(a.href) !== noHash(to)) return false;
    const r = a.getBoundingClientRect();
    if (r.bottom <= 0 || r.top >= innerHeight || r.width === 0) return false;
    try {
      sessionStorage.setItem(NAV_KEY, noHash(to));
    } catch {
      return false; // the new page could not tell it should play along
    }
    a.style.viewTransitionName = 'nav-sheet';
    vt.finished.finally(() => (a.style.viewTransitionName = ''));
    return true;
  }

  // The new page's half: a sheet covering the viewport for the link to grow into.
  function addNavSheet(vt: VT): void {
    const sheet = document.createElement('div');
    sheet.style.cssText = 'position:fixed;inset:0;pointer-events:none;view-transition-name:nav-sheet';
    document.documentElement.append(sheet);
    document.documentElement.classList.add('nav-vt');
    vt.finished.finally(() => {
      sheet.remove();
      document.documentElement.classList.remove('nav-vt');
    });
  }

  addEventListener('pageswap', (e) => {
    try {
      sessionStorage.setItem(FROM_KEY, location.href);
    } catch {
      /* storage is optional; the Navigation API usually covers it */
    }
    const vt = (e as Event & { viewTransition?: VT | null }).viewTransition;
    if (!vt) return;
    // Skipping rejects `ready`; unhandled, that is an error in every visitor's console.
    vt.ready.catch(() => {});
    const act = (e as Event & { activation?: { entry?: { url?: string } } | null }).activation;
    const to = act?.entry?.url || clicked;
    const here = kindOf(location.href);
    const dest = to ? kindOf(to) : 'other';
    if (reduced()) return vt.skipTransition();
    if (to && nameNavLink(to, vt)) return;
    if (here === 'catalogue' && dest === 'font') {
      const slug = slugOf(to);
      if (!slug || !nameCard(slug, vt)) vt.skipTransition();
    } else if (!(here === 'font' && dest === 'catalogue')) vt.skipTransition();
  });

  addEventListener('pagereveal', (e) => {
    let stored = '';
    let navTo = '';
    try {
      stored = sessionStorage.getItem(FROM_KEY) ?? '';
      navTo = sessionStorage.getItem(NAV_KEY) ?? '';
      sessionStorage.removeItem(FROM_KEY);
      sessionStorage.removeItem(NAV_KEY);
    } catch {
      /* see above */
    }
    const vt = (e as Event & { viewTransition?: VT | null }).viewTransition;
    if (!vt) return;
    vt.ready.catch(() => {});
    const nav = typeof navigation === 'undefined' ? undefined : navigation;
    const from = nav?.activation?.from?.url || stored;
    const here = kindOf(location.href);
    const prev = from ? kindOf(from) : 'other';
    if (reduced()) return vt.skipTransition();
    if (navTo && navTo === noHash(location.href)) return addNavSheet(vt);
    if (prev === 'catalogue' && here === 'font') return; // the font page's names are static
    // A freshly loaded grid with a query in the URL is re-sorted once the island
    // hydrates, so its server-rendered card positions can't be trusted.
    if (prev === 'font' && here === 'catalogue' && (restored || !location.search)) {
      const slug = slugOf(from);
      if (slug && nameCard(slug, vt)) return;
    }
    vt.skipTransition();
  });
}

/** Classic-script source that installs the page transitions; inlined in <head>. */
export function pageTransitionScript(base: string, langs: readonly string[]): string {
  const cfg: Config = { base, langs };
  return `(function(){${pageKind};${fontSlug};(${installPageTransitions})(${JSON.stringify(cfg)});})();`;
}
