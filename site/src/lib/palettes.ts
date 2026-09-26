/** Colour palettes of the theme menu. The full palettes live in
 * styles/tokens.css (`:root[data-palette=…]`, the default one on `:root`);
 * this holds what the menu's swatches draw — each variant's paper and accent —
 * and palettes.test.ts keeps the two in step. */

export const PALETTES = ['red', 'green', 'blue', 'amber', 'violet'] as const;
export type Palette = (typeof PALETTES)[number];
export type Mode = 'light' | 'dark';
export const DEFAULT_PALETTE: Palette = 'red';

export const SWATCHES: Record<Palette, Record<Mode, { paper: string; accent: string }>> = {
  red: {
    light: { paper: '#f6f2e9', accent: '#ac2c2a' },
    dark: { paper: '#151310', accent: '#f0786c' },
  },
  green: {
    light: { paper: '#eff3ec', accent: '#1b6a4b' },
    dark: { paper: '#0f1512', accent: '#5cc49a' },
  },
  blue: {
    light: { paper: '#eef1f6', accent: '#2c55a5' },
    dark: { paper: '#0f1219', accent: '#80a8f6' },
  },
  amber: {
    light: { paper: '#f7f1e2', accent: '#8f5200' },
    dark: { paper: '#16130b', accent: '#e6a748' },
  },
  violet: {
    light: { paper: '#f3f0f6', accent: '#7240a6' },
    dark: { paper: '#131019', accent: '#bd9df3' },
  },
};
