// Keep the one published copy of font files beside the site for downloads and previews.
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, unlinkSync, utimesSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { basename, join } from 'node:path';

const source = fileURLToPath(new URL('../../dist-downloads/', import.meta.url));
const target = fileURLToPath(new URL('../public/downloads/', import.meta.url));
if (!existsSync(join(source, 'manifest.json'))) {
  throw new Error('Font downloads are missing. Run make fonts first.');
}
const manifest = JSON.parse(readFileSync(join(source, 'manifest.json'), 'utf8'));
const keep = new Set(['manifest.json', ...manifest.entries.map((entry) => entry.file)]);
mkdirSync(target, { recursive: true });
for (const name of keep) {
  if (basename(name) !== name) throw new Error(`Invalid download filename: ${name}`);
  const src = join(source, name), dest = join(target, name);
  const info = statSync(src);
  const old = existsSync(dest) ? statSync(dest) : null;
  if (old && old.size === info.size && Math.abs(old.mtimeMs - info.mtimeMs) < 1) continue;
  copyFileSync(src, dest);
  utimesSync(dest, info.atime, info.mtime);
}
for (const name of readdirSync(target)) {
  if (!keep.has(name) && statSync(join(target, name)).isFile()) unlinkSync(join(target, name));
}
console.log(`Prepared ${keep.size} download files for the same Pages project.`);
