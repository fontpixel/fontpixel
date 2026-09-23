import { describe, expect, test } from 'vitest';
import { fontSlug, pageKind, pageTransitionScript, revealPercent, revealRadius, transformOffset } from './viewtransition';

const LANGS = ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr'];

describe('pageKind', () => {
  test.each([
    ['/en/', 'catalogue'],
    ['/zh-Hant/', 'catalogue'],
    ['/ja/page/3/', 'catalogue'],
    ['/en/fonts/galmuri/', 'font'],
    ['/fr/fonts/uw-ttyp0', 'font'],
    ['/', 'other'],
    ['/en/about/', 'other'],
    ['/en/compare/', 'other'],
    ['/en/fonts/', 'other'],
    ['/de/fonts/galmuri/', 'other'],
    ['/en/bdf-spec/intro/', 'other'],
  ])('%s → %s', (path, kind) => {
    expect(pageKind(path, '/', LANGS)).toBe(kind);
  });

  test('honours a base path', () => {
    expect(pageKind('/opf/en/', '/opf/', LANGS)).toBe('catalogue');
    expect(pageKind('/opf/en/fonts/galmuri/', '/opf', LANGS)).toBe('font');
    expect(pageKind('/en/fonts/galmuri/', '/opf/', LANGS)).toBe('other');
    expect(pageKind('/opfx/en/', '/opf/', LANGS)).toBe('other');
  });
});

describe('fontSlug', () => {
  test('extracts and decodes the slug', () => {
    expect(fontSlug('/en/fonts/galmuri/', '/', LANGS)).toBe('galmuri');
    expect(fontSlug('/opf/zh/fonts/a%20b/', '/opf/', LANGS)).toBe('a b');
  });
  test('is null elsewhere', () => {
    expect(fontSlug('/en/', '/', LANGS)).toBeNull();
    expect(fontSlug('/en/fonts/%E0%A4%A/', '/', LANGS)).toBeNull(); // malformed escape
  });
});

describe('revealRadius', () => {
  test('reaches the farthest corner', () => {
    expect(revealRadius(0, 0, 300, 400)).toBe(500);
    expect(revealRadius(290, 10, 300, 400)).toBe(Math.ceil(Math.hypot(290, 390)));
    expect(revealRadius(150, 200, 300, 400)).toBe(250);
  });
});

describe('revealPercent', () => {
  test('is relative to the diagonal over √2', () => {
    expect(revealPercent(Math.hypot(300, 400) / Math.SQRT2, 300, 400)).toBeCloseTo(100);
    // Reaching the far corner of a square from one corner takes √2 × 100%.
    expect(revealPercent(revealRadius(0, 0, 500, 500), 500, 500)).toBeCloseTo(Math.SQRT2 * 100, 0);
  });
});

describe('transformOffset', () => {
  test('reads the translation of 2D and 3D matrices', () => {
    expect(transformOffset('matrix(1, 0, 0, 1, 1174.5, -28)')).toEqual([1174.5, -28]);
    expect(transformOffset('matrix3d(1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 12, 34, 0, 1)')).toEqual([12, 34]);
  });
  test('is null for none or junk', () => {
    expect(transformOffset('none')).toBeNull();
    expect(transformOffset('')).toBeNull();
    expect(transformOffset('matrix(1, 0, 0, 1, a, 2)')).toBeNull();
    expect(transformOffset('matrix(1, 0, 0)')).toBeNull();
  });
});

/* ---- The serialized installer, run against a minimal fake browser ---- */

interface FakeEl {
  style: { viewTransitionName: string };
  top: number;
  children: Record<string, FakeEl>;
}

function makeEl(top = 100): FakeEl {
  return { style: { viewTransitionName: '' }, top, children: {} };
}

function run(href: string, opts: { reduced?: boolean; card?: FakeEl | null; activationFrom?: string } = {}) {
  const handlers: Record<string, (e: unknown) => void> = {};
  const storage = new Map<string, string>();
  const card = opts.card;
  const env = {
    addEventListener: (type: string, fn: (e: unknown) => void) => {
      handlers[type] = fn;
    },
    location: new URL(href),
    innerHeight: 800,
    matchMedia: () => ({ matches: Boolean(opts.reduced) }),
    CSS: { escape: (s: string) => s },
    sessionStorage: {
      getItem: (k: string) => storage.get(k) ?? null,
      setItem: (k: string, v: string) => void storage.set(k, v),
      removeItem: (k: string) => void storage.delete(k),
    },
    navigation: opts.activationFrom ? { activation: { from: { url: opts.activationFrom } } } : undefined,
    document: {
      querySelector: (sel: string) => {
        if (!card || !sel.startsWith('.card[')) return null;
        return {
          ...card,
          getBoundingClientRect: () => ({ top: card.top, bottom: card.top + 200, width: 300 }),
          querySelector: (s: string) => card.children[s] ?? null,
        };
      },
    },
  };
  const names = Object.keys(env);
  // The script refers to browser globals by bare name; shadow them with parameters.
  const fn = new Function(...names, pageTransitionScript('/', LANGS));
  (fn as (...a: unknown[]) => void)(...names.map((n) => env[n as keyof typeof env]));
  return { handlers, storage };
}

function fakeVT() {
  let resolve!: () => void;
  const vt = {
    skipped: false,
    ready: Promise.resolve(),
    finished: new Promise<void>((r) => (resolve = r)),
    skipTransition() {
      vt.skipped = true;
    },
  };
  return { vt, finish: () => resolve() };
}

describe('installPageTransitions (serialized)', () => {
  test('names the clicked card when a catalogue card opens its font page', async () => {
    const card = makeEl();
    const name = makeEl();
    const preview = makeEl();
    card.children['[data-vt="name"]'] = name;
    card.children['[data-vt="preview"]'] = preview;
    const { handlers, storage } = run('https://x.test/en/?q=pixel', { card });
    const { vt, finish } = fakeVT();
    handlers.pageswap!({ viewTransition: vt, activation: { entry: { url: 'https://x.test/en/fonts/galmuri/' } } });
    expect(vt.skipped).toBe(false);
    expect([card, name, preview].map((e) => e.style.viewTransitionName)).toEqual([
      'font-card',
      'font-name',
      'font-preview',
    ]);
    expect(storage.get('opf-vt-from')).toBe('https://x.test/en/?q=pixel');
    finish();
    await vt.finished;
    await Promise.resolve();
    expect(card.style.viewTransitionName).toBe('');
  });

  test('skips every other navigation', () => {
    const { handlers } = run('https://x.test/en/', { card: makeEl() });
    const { vt } = fakeVT();
    handlers.pageswap!({ viewTransition: vt, activation: { entry: { url: 'https://x.test/en/page/2/' } } });
    expect(vt.skipped).toBe(true);
  });

  test('skips when the card is off screen', () => {
    const { handlers } = run('https://x.test/en/', { card: makeEl(-500) });
    const { vt } = fakeVT();
    handlers.pageswap!({ viewTransition: vt, activation: { entry: { url: 'https://x.test/en/fonts/galmuri/' } } });
    expect(vt.skipped).toBe(true);
  });

  test('skips under reduced motion', () => {
    const { handlers } = run('https://x.test/en/', { card: makeEl(), reduced: true });
    const { vt } = fakeVT();
    handlers.pageswap!({ viewTransition: vt, activation: { entry: { url: 'https://x.test/en/fonts/galmuri/' } } });
    expect(vt.skipped).toBe(true);
  });

  test('the font page keeps an incoming transition from the catalogue', () => {
    const { handlers } = run('https://x.test/en/fonts/galmuri/', { activationFrom: 'https://x.test/en/' });
    const { vt } = fakeVT();
    handlers.pagereveal!({ viewTransition: vt });
    expect(vt.skipped).toBe(false);
  });

  test('returning to the grid names the card the font page belongs to', () => {
    const card = makeEl();
    const { handlers } = run('https://x.test/en/', { card, activationFrom: 'https://x.test/en/fonts/galmuri/' });
    const { vt } = fakeVT();
    handlers.pagereveal!({ viewTransition: vt });
    expect(vt.skipped).toBe(false);
    expect(card.style.viewTransitionName).toBe('font-card');
  });

  test('a freshly loaded grid with a query is not trusted, a bfcache-restored one is', () => {
    const fresh = run('https://x.test/en/?q=a', { card: makeEl(), activationFrom: 'https://x.test/en/fonts/galmuri/' });
    const a = fakeVT();
    fresh.handlers.pagereveal!({ viewTransition: a.vt });
    expect(a.vt.skipped).toBe(true);

    const back = run('https://x.test/en/?q=a', { card: makeEl(), activationFrom: 'https://x.test/en/fonts/galmuri/' });
    back.handlers.pageshow!({ persisted: true });
    const b = fakeVT();
    back.handlers.pagereveal!({ viewTransition: b.vt });
    expect(b.vt.skipped).toBe(false);
  });

  test('falls back to the stored previous URL without the Navigation API', () => {
    const { handlers, storage } = run('https://x.test/en/fonts/galmuri/');
    storage.set('opf-vt-from', 'https://x.test/en/');
    const { vt } = fakeVT();
    handlers.pagereveal!({ viewTransition: vt });
    expect(vt.skipped).toBe(false);
    expect(storage.has('opf-vt-from')).toBe(false);
  });
});
