<script lang="ts">
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { formatCp } from '../lib/format';
  import type { DecodedGlyph } from '../lib/glyphpack';
  import { rowBytes } from '../lib/glyphpack';
  import { GlyphStore, type VariantManifest } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import type { UIStrings } from '../i18n/types';

  interface Props {
    slug: string;
    variantIds: string[];
    s: UIStrings;
    dataBase: string;
  }
  const { slug, variantIds, s, dataBase }: Props = $props();

  const store = new GlyphStore(dataBase);
  let variantId = $state(variantIds[0]!);
  let manifest = $state<VariantManifest | null>(null);
  let rangeIdx = $state(0);
  let themeTick = $state(0);
  let inspected = $state<DecodedGlyph | null>(null);
  let inspectorCanvas: HTMLCanvasElement | undefined = $state();

  onMount(() => {
    const onVariant = (e: Event) => {
      const id = (e as CustomEvent).detail?.id;
      if (id && variantIds.includes(id)) {
        variantId = id;
        rangeIdx = 0;
        inspected = null;
      }
    };
    document.addEventListener('fbf:variantchange', onVariant);
    const off = onThemeChange(() => (themeTick += 1));
    return () => {
      document.removeEventListener('fbf:variantchange', onVariant);
      off();
    };
  });

  $effect(() => {
    const vid = variantId;
    store
      .loadManifest(slug, vid)
      .then((m) => (manifest = m))
      .catch((e) => console.error(e));
  });

  const range = $derived(manifest?.ranges[rangeIdx] ?? null);
  const blocks = $derived.by(() => {
    if (!range) return [];
    const out: number[] = [];
    for (let b = range.start; b < range.end; b += 256) out.push(b);
    return out;
  });

  function rangeLabel(r: { start: number; end: number; glyphs: number }): string {
    return `${formatCp(r.start)}–${formatCp(r.end - 1)} (${r.glyphs})`;
  }

  function drawSheet(canvas: HTMLCanvasElement, blockStart: number) {
    const m = manifest;
    const r = range;
    if (!m || !r) return;
    const cell = Math.max(m.ascent + m.descent + 3, 10);
    const cols = 16;
    const rows = 16;
    void themeTick;
    store
      .loadChunk(slug, variantId, r.file)
      .then((chunk) => {
        const { ink, paper } = themeInkPaper();
        canvas.width = cols * cell;
        canvas.height = rows * cell;
        const ctx = canvas.getContext('2d')!;
        const img = ctx.createImageData(canvas.width, canvas.height);
        const put = (x: number, y: number, c: readonly number[]) => {
          const i = (y * canvas.width + x) * 4;
          img.data[i] = c[0]!;
          img.data[i + 1] = c[1]!;
          img.data[i + 2] = c[2]!;
          img.data[i + 3] = 255;
        };
        for (let y = 0; y < canvas.height; y++)
          for (let x = 0; x < canvas.width; x++) put(x, y, paper);
        for (let i = 0; i < 256; i++) {
          const cp = blockStart + i;
          const g = chunk.get(cp);
          if (!g) continue;
          const cx = (i % cols) * cell + 1;
          const baseline = Math.floor(i / cols) * cell + 1 + m.ascent;
          const nb = rowBytes(g.w);
          const top = baseline - (g.yoff + g.h);
          for (let yy = 0; yy < g.h; yy++) {
            for (let xx = 0; xx < g.w; xx++) {
              if (g.rows[yy * nb + (xx >> 3)]! & (0x80 >> (xx & 7))) {
                const px = cx + g.xoff + xx;
                const py = top + yy;
                if (px >= 0 && py >= 0 && px < canvas.width && py < canvas.height) {
                  put(px, py, ink);
                }
              }
            }
          }
        }
        ctx.putImageData(img, 0, 0);
        canvas.dataset['cell'] = String(cell);
        canvas.dataset['block'] = String(blockStart);
      })
      .catch((e) => console.error(e));
  }

  function sheetAction(canvas: HTMLCanvasElement, blockStart: number) {
    // svelte action：可见时绘制，主题/变体变化时由 #key 重建
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        drawSheet(canvas, blockStart);
        io.disconnect();
      }
    });
    io.observe(canvas);
    return { destroy: () => io.disconnect() };
  }

  function onSheetClick(e: MouseEvent) {
    const canvas = e.currentTarget as HTMLCanvasElement;
    const cell = Number(canvas.dataset['cell'] ?? 0);
    const blockStart = Number(canvas.dataset['block'] ?? 0);
    if (!cell || !manifest || !range) return;
    const rect = canvas.getBoundingClientRect();
    const scale = rect.width / canvas.width;
    const col = Math.floor((e.clientX - rect.left) / scale / cell);
    const row = Math.floor((e.clientY - rect.top) / scale / cell);
    const cp = blockStart + row * 16 + col;
    store
      .loadChunk(slug, variantId, range.file)
      .then((chunk) => {
        inspected = chunk.get(cp);
      })
      .catch(() => {});
  }

  $effect(() => {
    const g = inspected;
    const m = manifest;
    if (!g || !m || !inspectorCanvas) return;
    void themeTick;
    const { ink, paper } = themeInkPaper();
    const map = new Map([[g.cp, g]]);
    const r = rasterize(String.fromCodePoint(g.cp), map, m, {
      invert: false,
      highlightMissing: false,
      ink,
      paper,
    });
    paint(inspectorCanvas, r, 8, { grid: true });
  });

  function inkSize(g: DecodedGlyph): string {
    const nb = rowBytes(g.w);
    let minX = g.w, maxX = -1, minY = g.h, maxY = -1;
    for (let y = 0; y < g.h; y++)
      for (let x = 0; x < g.w; x++)
        if (g.rows[y * nb + (x >> 3)]! & (0x80 >> (x & 7))) {
          if (x < minX) minX = x;
          if (x > maxX) maxX = x;
          if (y < minY) minY = y;
          if (y > maxY) maxY = y;
        }
    return maxX < 0 ? '—' : `${maxX - minX + 1}×${maxY - minY + 1}`;
  }
</script>

<section class="gg" data-testid="glyph-grid">
  <div class="gg__bar">
    <h2>{s.detail.glyphGridTitle}</h2>
    {#if manifest}
      <label class="gg__jump"
        >{s.detail.glyphGridJump}
        <select bind:value={rangeIdx} data-testid="range-select">
          {#each manifest.ranges as r, i (r.file)}
            <option value={i}>{rangeLabel(r)}</option>
          {/each}
        </select>
      </label>
    {/if}
  </div>

  {#if inspected}
    {@const g = inspected}
    <div class="gg__inspector" data-testid="glyph-inspector">
      <canvas bind:this={inspectorCanvas}></canvas>
      <dl class="mono">
        <dt>{s.detail.inspectorCp}</dt>
        <dd>{formatCp(g.cp)} <span class="gg__char">{String.fromCodePoint(g.cp)}</span></dd>
        <dt>{s.detail.inspectorAdvance}</dt>
        <dd>{g.dwidth}px</dd>
        <dt>{s.detail.inspectorBbx}</dt>
        <dd>{g.w}×{g.h} @ {g.xoff},{g.yoff}</dd>
        <dt>{s.detail.inspectorInk}</dt>
        <dd>{inkSize(g)}</dd>
      </dl>
      <button type="button" class="gg__close" onclick={() => (inspected = null)}>×</button>
    </div>
  {/if}

  <div class="gg__sheets">
    {#key `${variantId}:${rangeIdx}:${themeTick}`}
      {#each blocks as b (b)}
        <figure class="gg__sheet">
          <figcaption class="mono">{formatCp(b)}</figcaption>
          <canvas use:sheetAction={b} onclick={onSheetClick}></canvas>
        </figure>
      {/each}
    {/key}
  </div>
</section>

<style>
  .gg__bar {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--s4);
    flex-wrap: wrap;
  }
  .gg__bar h2 {
    font-size: 1rem;
    margin: 0 0 var(--s3);
  }
  .gg__jump {
    font-size: 0.82rem;
    color: var(--ink-2);
  }
  .gg__sheets {
    display: flex;
    flex-wrap: wrap;
    gap: var(--s4);
  }
  .gg__sheet {
    margin: 0;
  }
  .gg__sheet figcaption {
    font-size: 0.7rem;
    color: var(--ink-3);
    margin-bottom: 2px;
  }
  .gg__sheet canvas {
    border: 1px solid var(--line);
    image-rendering: pixelated;
    width: 288px;
    max-width: 100%;
    cursor: crosshair;
    background: var(--surface);
  }
  .gg__inspector {
    position: relative;
    display: flex;
    gap: var(--s5);
    align-items: center;
    border: 1px solid var(--line);
    background: var(--surface);
    padding: var(--s4);
    margin-bottom: var(--s4);
  }
  .gg__inspector canvas {
    image-rendering: pixelated;
    max-width: 12rem;
  }
  .gg__inspector dl {
    display: grid;
    grid-template-columns: auto 1fr;
    gap: var(--s1) var(--s4);
    font-size: 0.82rem;
    margin: 0;
  }
  .gg__inspector dt {
    color: var(--ink-3);
  }
  .gg__inspector dd {
    margin: 0;
  }
  .gg__char {
    font-size: 1.2rem;
    margin-left: var(--s2);
  }
  .gg__close {
    position: absolute;
    top: var(--s2);
    right: var(--s2);
    border: none;
    font-size: 1rem;
    color: var(--ink-3);
  }
</style>
