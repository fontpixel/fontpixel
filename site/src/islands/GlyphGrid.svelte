<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { formatCp } from '../lib/format';
  import type { DecodedGlyph } from '../lib/bitmap';
  import { rowBytes } from '../lib/bitmap';
  import { getGlyphStore } from '../lib/glyphstore';
  import type { BitmapFont } from '../lib/bitmap';
  import { paint, rasterize } from '../lib/render';
  import type { UIStrings } from '../i18n/types';
  import { UNICODE_BLOCKS } from '../lib/unicodeblocks';

  interface Props {
    slug: string;
    variantIds: string[];
    initialVariant: string;
    s: UIStrings;
    dataBase: string;
    /** Names of the Unicode blocks each variant actually covers (has at least one glyph in) */
    blocksByVariant: Record<string, string[]>;
  }
  const { slug, variantIds, s, dataBase, blocksByVariant, initialVariant }: Props = $props();

  const store = getGlyphStore(dataBase);
  let variantId = $state(initialVariant);
  let manifest = $state<BitmapFont | null>(null);
  let selection = $state('r:0');
  let jumpQuery = $state('');
  let themeTick = $state(0);
  let inspected = $state<DecodedGlyph | null>(null);
  let activeCp = $state<number | null>(null);
  let inspector: HTMLDivElement | undefined = $state();
  let returnFocus: HTMLCanvasElement | null = null;
  const sheetCps = (start: number, count: number) => [...(manifest?.glyphs.keys() ?? [])]
    .filter(cp => cp >= start && cp < start + count).sort((a, b) => a - b);
  async function inspect(cp: number, canvas: HTMLCanvasElement) {
    inspected = manifest?.glyphs.get(cp) ?? null;
    activeCp = cp;
    returnFocus = canvas;
    if (inspected) { await tick(); inspector?.focus(); }
  }
  function closeInspector() {
    inspected = null;
    returnFocus?.focus();
  }
  function sheetKey(event: KeyboardEvent, start: number, count: number) {
    const cps = sheetCps(start, count);
    if (!cps.length) return;
    const cp = activeCp != null && cps.includes(activeCp) ? activeCp : cps[0]!;
    const index = cps.indexOf(cp);
    let next: number | undefined;
    if (event.key === 'ArrowRight') next = cps[Math.min(index + 1, cps.length - 1)];
    else if (event.key === 'ArrowLeft') next = cps[Math.max(index - 1, 0)];
    else if (event.key === 'ArrowDown') next = cps.find(c => c >= cp + 16) ?? cps.at(-1);
    else if (event.key === 'ArrowUp') next = [...cps].reverse().find(c => c <= cp - 16) ?? cps[0];
    else if (event.key === 'Home') next = cps[0];
    else if (event.key === 'End') next = cps.at(-1);
    else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      void inspect(cp, event.currentTarget as HTMLCanvasElement);
      return;
    }
    if (next != null) { event.preventDefault(); activeCp = next; }
  }
  let inspectorCanvas: HTMLCanvasElement | undefined = $state();

  onMount(() => {
    // This island hydrates on scroll, after the editor may have changed variants.
    const current = document.querySelector<HTMLSelectElement>('[name="sample-variant"]')?.value;
    if (current && variantIds.includes(current)) variantId = current;
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
    manifest = null;
    store
      .loadFont(slug, vid)
      .then((m) => { if (variantId === vid) manifest = m; })
      .catch((e) => console.error(e));
  });

  // The dropdown holds occupied 256-codepoint ranges and Unicode blocks;
  // both resolve to a single [start, end) code point span.
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
  // At most 256 code points per page. Pagination is counted from the span's start
  // and truncated at its end — selecting a block should draw only that block, not
  // pull in a neighboring block just because 256-alignment overruns into it
  // (e.g. Hiragana U+3040–U+309F, aligned to 256, would drag in CJK Symbols and Katakana).
  const sheets = $derived.by(() => {
    if (!span) return [];
    const out: { start: number; count: number }[] = [];
    for (let b = span[0]; b < span[1]; b += 256)
      out.push({ start: b, count: Math.min(256, span[1] - b) });
    return out;
  });
  const coveredBlocks = $derived(
    (blocksByVariant[variantId] ?? [])
      .filter((n) => UNICODE_BLOCKS[n])
      .sort((a, b) => UNICODE_BLOCKS[a]![0] - UNICODE_BLOCKS[b]![0]),
  );

  // The dropdown can easily have dozens or hundreds of entries, so give it a live-filter search box.
  // Both name and code point are searchable: type "hira" to find Hiragana, type "4e00" to find where CJK Han starts.
  const q = $derived(jumpQuery.trim().toLowerCase());
  const matches = (text: string, cps: number[]) =>
    !q ||
    text.toLowerCase().includes(q) ||
    cps.some((c) => c.toString(16).padStart(4, '0').includes(q));
  const shownRanges = $derived(
    (manifest?.ranges ?? []).map((r, i) => ({ r, i })).filter(
      // Always keep the currently selected item, otherwise the dropdown would show blank while searching
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
    const vid = variantId;
    if (!m) return;
    const cell = Math.max(m.ascent + m.descent + 3, 10);
    const cols = 16;
    const rows = Math.ceil(sheet.count / cols);
    void themeTick;
    store
      .loadFont(slug, variantId)
      .then((chunk) => {
        if (variantId !== vid || !canvas.isConnected) return;
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
          const g = chunk.glyphs.get(cp) ?? null;
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
    // Svelte action: draws when visible; rebuilt via #key when theme/variant changes
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
    void inspect(cp, canvas);
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

<section id="glyph-grid" class="gg" data-testid="glyph-grid">
  <div class="gg__bar">
    <h2>{s.detail.glyphGridTitle}</h2>
    {#if manifest}
      <div class="gg__jump">
        <input
          class="gg__search"
          type="search"
          name="glyph-search"
          bind:value={jumpQuery}
          placeholder={s.detail.glyphGridSearch}
          aria-label={s.detail.glyphGridSearch}
          data-testid="range-search"
        />
        <label
          >{s.detail.glyphGridJump}
          <select name="glyph-range" bind:value={selection} data-testid="range-select">
            {#each shownRanges as { r, i } (r.start)}
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
    <div class="gg__inspector" data-testid="glyph-inspector" bind:this={inspector} tabindex="-1" role="group" aria-label={`${s.detail.inspectorCp} ${formatCp(g.cp)}`} onkeydown={(event) => { if (event.key === 'Escape') { event.preventDefault(); closeInspector(); } }}>
      <canvas bind:this={inspectorCanvas} role="img" aria-label={`${s.detail.glyphGridTitle}: ${formatCp(g.cp)}`}></canvas>
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
        onclick={closeInspector}>×</button>
    </div>
  {/if}

  <p id="glyph-keyboard-help" class="gg__help">{s.detail.glyphGridKeyboard}</p>
  <div class="gg__sheets">
    {#key `${variantId}:${selection}:${themeTick}`}
      {#each sheets as sh (sh.start)}
        {@const selected = activeCp != null && activeCp >= sh.start && activeCp < sh.start + sh.count ? activeCp : sheetCps(sh.start, sh.count)[0]}
        <figure class="gg__sheet">
          <figcaption class="mono">{formatCp(sh.start)}</figcaption>
          <div class="gg__sheet-image">
            <canvas use:sheetAction={sh} onclick={onSheetClick} role="button" tabindex="0"
              aria-label={`${s.detail.glyphGridTitle}: ${formatCp(selected ?? sh.start)}`}
              aria-describedby="glyph-keyboard-help"
              onfocus={() => { activeCp = selected ?? sh.start; }}
              onkeydown={(event) => sheetKey(event, sh.start, sh.count)}></canvas>
            {#if selected != null}
              <span class="gg__cursor" aria-hidden="true"
                style:left={`${((selected - sh.start) % 16) / 16 * 100}%`}
                style:top={`${Math.floor((selected - sh.start) / 16) / Math.ceil(sh.count / 16) * 100}%`}
                style:height={`${100 / Math.ceil(sh.count / 16)}%`}></span>
            {/if}
          </div>
        </figure>
      {/each}
    {/key}
  </div>
</section>

<style>
  .gg__help { color: var(--ink-2); font-size: 0.8rem; }
  .gg__sheet-image { position: relative; width: fit-content; max-width: 100%; }
  .gg__cursor { display: none; position: absolute; width: 6.25%; border: 2px solid var(--accent); pointer-events: none; }
  .gg__sheet-image:focus-within .gg__cursor { display: block; }
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
  /* 3 sheets per row on large screens, filling the container; narrows to 2 columns then 1 on smaller screens */
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
    font-size: 0.75rem;
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
