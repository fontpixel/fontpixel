/** Combine adjacent one-pixel ink runs into one path without changing any pixels.
 * This keeps inline SVG previews themeable while avoiding thousands of DOM nodes.
 * Missing-glyph outlines and any other SVG markup are preserved in their original order.
 */
export function compactPreviewSvg(svg: string): string {
  return svg.replace(/(?:<rect x="-?\d+" y="-?\d+" width="\d+" height="1" fill="currentColor"\/>)+/g, (runs) => {
    const path = [...runs.matchAll(/x="(-?\d+)" y="(-?\d+)" width="(\d+)"/g)]
      .map(([, x, y, width]) => `M${x} ${y}h${width}v1h-${width}z`).join('');
    return `<path d="${path}" fill="currentColor"/>`;
  });
}
