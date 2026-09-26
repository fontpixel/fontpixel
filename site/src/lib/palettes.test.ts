import { readFileSync } from 'node:fs';
import { expect, test } from 'vitest';
import { PALETTES, SWATCHES, type Mode, type Palette } from './palettes';

const css = readFileSync(new URL('../styles/tokens.css', import.meta.url), 'utf-8');

/** Custom properties of the one rule whose selector is exactly `selector`. */
function rule(selector: string): Record<string, string> {
  const start = css.indexOf(`\n${selector} {`);
  expect(start, selector).toBeGreaterThanOrEqual(0);
  const body = css.slice(css.indexOf('{', start) + 1, css.indexOf('}', start));
  return Object.fromEntries([...body.matchAll(/(--[\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2]!.trim()]));
}

function tokens(palette: Palette, mode: Mode): Record<string, string> {
  if (palette === 'red') {
    return mode === 'light' ? rule(':root') : { ...rule(':root'), ...rule(":root[data-theme='dark']") };
  }
  const light = rule(`:root[data-palette='${palette}']`);
  return mode === 'light' ? light : rule(`:root[data-palette='${palette}'][data-theme='dark']`);
}

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = Number.parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r! + 0.7152 * g! + 0.0722 * b!;
}
function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi! + 0.05) / (lo! + 0.05);
}

/** The docs pages' body text (DocsLayout's --dx-text) */
const DOC_TEXT: Record<Mode, string> = { light: '#1c1e21', dark: '#ececec' };

for (const palette of PALETTES) {
  for (const mode of ['light', 'dark'] as const) {
    test(`${palette} ${mode}: every text colour meets WCAG AA`, () => {
      const t = tokens(palette, mode);
      for (const bg of [t['--paper']!, t['--surface']!]) {
        for (const fg of ['--ink', '--ink-2', '--ink-3', '--accent']) {
          expect(contrast(t[fg]!, bg), `${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
        }
        expect(contrast(t['--doc-link']!, bg), `--doc-link on ${bg}`).toBeGreaterThanOrEqual(4.5);
      }
      expect(contrast(t['--on-accent']!, t['--accent']!)).toBeGreaterThanOrEqual(4.5);
      // Docs links go without an underline; colour alone has to set them apart.
      expect(contrast(t['--doc-link']!, DOC_TEXT[mode])).toBeGreaterThanOrEqual(3);
    });

    test(`${palette} ${mode}: the theme menu's swatch matches the palette`, () => {
      const t = tokens(palette, mode);
      expect(SWATCHES[palette][mode]).toEqual({ paper: t['--paper'], accent: t['--accent'] });
    });
  }
}
