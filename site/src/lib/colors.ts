/** Read the canvas theme colors from CSS variables. */

import type { Rgba } from './render';

function parseHex(v: string): Rgba | null {
  const m = v.trim().match(/^#([0-9a-f]{6})$/i);
  if (!m) return null;
  const n = Number.parseInt(m[1]!, 16);
  return [(n >> 16) & 0xff, (n >> 8) & 0xff, n & 0xff, 255];
}

export function themeInkPaper(): { ink: Rgba; paper: Rgba } {
  if (typeof document === 'undefined') {
    return { ink: [17, 17, 17, 255], paper: [250, 247, 240, 255] };
  }
  const cs = getComputedStyle(document.documentElement);
  return {
    ink: parseHex(cs.getPropertyValue('--canvas-ink')) ?? [17, 17, 17, 255],
    paper: parseHex(cs.getPropertyValue('--canvas-paper')) ?? [250, 247, 240, 255],
  };
}

export function onThemeChange(cb: () => void): () => void {
  const mo = new MutationObserver(cb);
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  return () => mo.disconnect();
}
