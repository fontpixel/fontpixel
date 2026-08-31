<script lang="ts">
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { formatCp } from '../lib/format';
  import type { DecodedGlyph } from '../lib/glyphpack';
  import { rowBytes } from '../lib/glyphpack';
  import { GlyphStore, type VariantManifest } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import type { UIStrings } from '../i18n/types';
  import { UNICODE_BLOCKS } from '../lib/unicodeblocks';

  interface Props {
    slug: string;
    variantIds: string[];
    s: UIStrings;
    dataBase: string;
    /** 每个变体实际覆盖到的 Unicode block 名（至少含一个字形） */
    blocksByVariant: Record<string, string[]>;
  }
  const { slug, variantIds, s, dataBase, blocksByVariant }: Props = $props();

  const store = new GlyphStore(dataBase);
  let variantId = $state(variantIds[0]!);
  let manifest = $state<VariantManifest | null>(null);
  let selection = $state('r:0');
  let jumpQuery = $state('');
  let themeTick = $state(0);
  let inspected = $state<DecodedGlyph | null>(null);
  let inspectorCanvas: HTMLCanvasElement | undefined = $state();

  onMount(() => {
    const onVariant = (e: Event) => {
      const id = (e as CustomEvent).detail?.id;
      if (id && variantIds.includes(id)) {
        variantId = id;
        selection = 'r:0';
        inspected = null;
      }
    };
    document.addEventListener('opf:variantchange', onVariant);
    const off = onThemeChange(() => (themeTick += 1));
    return () => {
      document.removeEventListener('opf:variantchange', onVariant);
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

  // 下拉里既有分块 range，也有该变体覆盖到的 Unicode block；两者都归结为
  // 一个 [start, end) 码位区间。
  const span = $derived.by((): [number, number] | null => {
    const m = manifest;
    if (!m) return null;
    if (selection.startsWith('b:')) {
      const b = UNICODE_BLOCKS[selection.slice(2)];
      return b ? [b[0], b[1] + 1] : null;
    }
    const r = m.ranges[Number(selection.slice(2))];
    return r ? [r.start, r.end] : null;
  });
  // 每页最多 256 个码位。分页从区间起点算起并在终点截断——选了某个 block
  // 就只画这个 block，不能因为按 256 对齐而把邻居 block 一起画进来
  // （如平假名 U+3040–U+309F 对齐后会带出 CJK 符号和片假名）。
  const sheets = $derived.by(() => {
    if (!span) return [];
    const out: { start: number; count: number }[] = [];
    for (let b = span[0]; b < span[1]; b += 256)
      out.push({ start: b, count: Math.min(256, span[1] - b) });
    return out;
  });
  /** 某个码位落在哪个分块文件里——block 可能横跨多个分块。 */
  function rangeFor(cp: number) {
    return manifest?.ranges.find((r) => cp >= r.start && cp < r.end) ?? null;
  }
  const coveredBlocks = $derived(
    (blocksByVariant[variantId] ?? [])
      .filter((n) => UNICODE_BLOCKS[n])
      .sort((a, b) => UNICODE_BLOCKS[a]![0] - UNICODE_BLOCKS[b]![0]),
  );

  // 下拉里动辄几十上百项，给个即输即筛的搜索框。名字和码位都能搜：
  // 输 "hira" 找平假名，输 "4e00" 找汉字起始的那一段。
  const q = $derived(jumpQuery.trim().toLowerCase());
  const matches = (text: string, cps: number[]) =>
    !q ||
    text.toLowerCase().includes(q) ||
    cps.some((c) => c.toString(16).padStart(4, '0').includes(q));
  const shownRanges = $derived(
    (manifest?.ranges ?? []).map((r, i) => ({ r, i })).filter(
      // 当前选中项始终保留，否则搜索时下拉会显示空白
      ({ r, i }) => selection === `r:${i}` || matches(rangeLabel(r), [r.start, r.end - 1]),
    ),
  );
  const shownBlocks = $derived(
    coveredBlocks.filter(
      (n) => selection === `b:${n}` || matches(n, [...UNICODE_BLOCKS[n]!]),
    ),
  );

  function rangeLabel(r: { start: number; end: number; glyphs: number }): string {
    return `${formatCp(r.start)}–${formatCp(r.end - 1)} (${r.glyphs})`;
  }

  function drawSheet(canvas: HTMLCanvasElement, sheet: { start: number; count: number }) {
    const m = manifest;
    const blockStart = sheet.start;
    const r = rangeFor(blockStart);
    if (!m || !r) return;
    const cell = Math.max(m.ascent + m.descent + 3, 10);
    const cols = 16;
    const rows = Math.ceil(sheet.count / cols);
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
        for (let i = 0; i < sheet.count; i++) {
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

  function sheetAction(canvas: HTMLCanvasElement, sheet: { start: number; count: number }) {
    // svelte action：可见时绘制，主题/变体变化时由 #key 重建
    const io = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting)) {
        drawSheet(canvas, sheet);
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
    if (!cell || !manifest) return;
    const rect = canvas.getBoundingClientRect();
    const scale = rect.width / canvas.width;
    const col = Math.floor((e.clientX - rect.left) / scale / cell);
    const row = Math.floor((e.clientY - rect.top) / scale / cell);
    const cp = blockStart + row * 16 + col;
    const r = rangeFor(blockStart);
    if (!r) return;
    store
      .loadChunk(slug, variantId, r.file)
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
      <div class="gg__jump">
        <input
          class="gg__search"
          type="search"
          bind:value={jumpQuery}
          placeholder={s.detail.glyphGridSearch}
          aria-label={s.detail.glyphGridSearch}
          data-testid="range-search"
        />
        <label
          >{s.detail.glyphGridJump}
          <select bind:value={selection} data-testid="range-select">
            {#each shownRanges as { r, i } (r.file)}
              <option value={`r:${i}`}>{rangeLabel(r)}</option>
            {/each}
          {#if shownBlocks.length > 0}
            <optgroup label={s.detail.glyphGridBlocks}>
              {#each shownBlocks as name (name)}
                <option value={`b:${name}`}
                  >{name} ({formatCp(UNICODE_BLOCKS[name]![0])}–{formatCp(
                    UNICODE_BLOCKS[name]![1],
                  )})</option
                >
              {/each}
            </optgroup>
          {/if}
          </select>
        </label>
      </div>
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
      <button type="button" class="gg__close" aria-label={s.detail.close}
        onclick={() => (inspected = null)}>×</button>
    </div>
  {/if}

  <div class="gg__sheets">
    {#key `${variantId}:${selection}:${themeTick}`}
      {#each sheets as sh (sh.start)}
        <figure class="gg__sheet">
          <figcaption class="mono">{formatCp(sh.start)}</figcaption>
          <canvas use:sheetAction={sh} onclick={onSheetClick}></canvas>
        </figure>
      {/each}
    {/key}
  </div>
</section>

<style>
  .gg {
    display: block;
    margin-bottom: var(--s6);
  }
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
    display: flex;
    align-items: center;
    gap: var(--s3);
    flex-wrap: wrap;
    font-size: 0.82rem;
    color: var(--ink-2);
  }
  .gg__search {
    width: 9rem;
    font-size: 0.8rem;
  }
  /* 大屏每行 3 张，铺满容器；窄屏依次降到 2 列、1 列 */
  .gg__sheets {
    display: grid;
    grid-template-columns: 1fr;
    gap: var(--s4);
  }
  @media (min-width: 560px) {
    .gg__sheets {
      grid-template-columns: repeat(2, 1fr);
    }
  }
  @media (min-width: 860px) {
    .gg__sheets {
      grid-template-columns: repeat(3, 1fr);
    }
  }
  .gg__sheet {
    margin: 0;
    min-width: 0;
  }
  .gg__sheet figcaption {
    font-size: 0.7rem;
    color: var(--ink-3);
    margin-bottom: 2px;
  }
  .gg__sheet canvas {
    border: 1px solid var(--line);
    image-rendering: pixelated;
    display: block;
    width: 100%;
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
