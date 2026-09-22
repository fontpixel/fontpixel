import { expect, test } from 'vitest';
import sharp from 'sharp';
import { compactPreviewSvg } from './svg-preview';

test('compact previews preserve rendered pixels, dimensions, and missing-glyph outlines', async () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" width="64" height="64" shape-rendering="crispEdges">'
    + '<rect x="-1" y="1" width="4" height="1" fill="currentColor"/>'
    + '<rect x="2" y="2" width="7" height="1" fill="currentColor"/>'
    + '<rect class="missing" x="10.5" y="2.5" width="3" height="8" fill="none" stroke="currentColor" stroke-dasharray="1 1"/>'
    + '<rect x="2" y="3" width="7" height="1" fill="currentColor"/></svg>';
  const compact = compactPreviewSvg(svg);
  for (const color of ['#1c1a17', '#e9e3d5']) {
    const render = (source: string) => sharp(Buffer.from(source.replace('<svg ', `<svg color="${color}" `))).raw().toBuffer({ resolveWithObject: true });
    const [before, after] = await Promise.all([render(svg), render(compact)]);
    expect(after.info).toEqual(before.info);
    expect(after.data).toEqual(before.data);
  }
  expect(compact).toContain('class="missing"');
  expect(compact.match(/<path/g)).toHaveLength(2);
  expect(compactPreviewSvg(compact)).toBe(compact);
});
