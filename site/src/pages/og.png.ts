import sharp from 'sharp';
import type { APIRoute } from 'astro';

// A deterministic site card, built as a static PNG; no image service at runtime.
export const GET: APIRoute = async () => {
  const pixels = ['11110', '10000', '10000', '11100', '10000', '10000', '10000'];
  const mark = pixels.flatMap((row, y) => [...row].flatMap((p, x) =>
    p === '1' ? [`<rect x="${80 + x * 22}" y="${142 + y * 22}" width="22" height="22"/>`] : [],
  )).join('');
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
    <rect width="1200" height="630" fill="#f6f2e9"/>
    <path d="M80 70H1120M80 540H1120" stroke="#d9d2c2" stroke-width="2"/>
    <g fill="#b5312f">${mark}</g>
    <g font-family="DejaVu Sans, sans-serif" fill="#1c1a17">
      <text x="238" y="261" font-size="98" font-weight="bold">FontPixel</text>
      <text x="80" y="383" font-size="38">Open-source pixel fonts.</text>
      <text x="80" y="438" font-size="28" fill="#4d4840">Explore · Type · Compare · Download</text>
      <text x="80" y="589" font-size="24" fill="#736d5e">fontpixel.com</text>
    </g>
  </svg>`;
  const png = await sharp(Buffer.from(svg)).png().toBuffer();
  return new Response(new Uint8Array(png), { headers: { 'Content-Type': 'image/png' } });
};
