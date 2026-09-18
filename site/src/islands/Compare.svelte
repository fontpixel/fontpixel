<script lang="ts">
  /** Side-by-side comparison: the same text and zoom, with no fixed slot limit.
   *
   * The collection's whole claim is that every font here was measured with one
   * ruler; this is that claim made visible. Everything is driven from the
   * catalogue index that the page already ships, so no extra build-time data is
   * needed, and the selection lives in the URL (?v=slug:variant,…) so a
   * comparison can be linked to.
   */
  import { onMount } from 'svelte';
  import type { FamilyIndex } from '../lib/schema';
  import type { UIStrings } from '../i18n/types';
  import { getGlyphStore } from '../lib/glyphstore';
  import { rasterize, paint } from '../lib/render';
  import { onThemeChange, themeInkPaper } from '../lib/colors';
  import { NOWRAP_PRESETS, SAMPLES, defaultSample, presetLabel } from '../lib/samples';
  import { variantLabels } from '../lib/variantlabel';
  import { previewFor } from '../lib/preview';
  import { highlightCode, type CodeLang } from '../lib/codehl';
  import { framePalette, type Frame } from '../lib/frames';
  import FrameControls from './FrameControls.svelte';
  import FrameShell from './FrameShell.svelte';
  import Icon from './Icon.svelte';

  interface Props {
    /** Catalogue order, including the current Auto rating. */
    families: FamilyIndex[];
    s: UIStrings;
    dataBase: string;
    lang: string;
    /** slug:variantId pairs to preselect, from the page's query string */
    initial: string[];
  }
  const { families, s, dataBase, lang, initial }: Props = $props();

  const store = getGlyphStore(dataBase);
  const bySlug = new Map(families.map((f) => [f.slug, f]));

  const nameOf = (f: FamilyIndex) => f.names[lang] ?? f.names.en ?? f.name;
  /** Families sorted by display name so the picker reads alphabetically. */
  const sorted = [...families].sort((a, b) => nameOf(a).localeCompare(nameOf(b)));

  type Slot = { slug: string; variantId: string };
  const parse = (pairs: string[]): Slot[] => {
    const out: Slot[] = [];
    for (const p of pairs) {
      const [slug, vid] = p.split(':');
      const fam = slug ? bySlug.get(slug) : undefined;
      if (!fam) continue;
      const variantId = fam.variants.find((x) => x.id === vid)?.id ?? previewFor(fam).variantId;
      out.push({ slug: fam.slug, variantId });
    }
    return out;
  };

  // The page is prerendered, so the query string can only be read here
  const fromUrl =
    typeof window === 'undefined'
      ? []
      : (new URL(window.location.href).searchParams.get('v') ?? '').split(',').filter(Boolean);
  let slots = $state<Slot[]>(parse(fromUrl.length ? fromUrl : initial));
  let text = $state('');
  let zoom = $state(3);
  // The same controls as the detail page's type-test box, minus the size ladder:
  // every column here is already a different variant, which is what the ladder
  // is for. They apply to all columns at once — a comparison that let the
  // columns differ in zoom or frame would be showing two variables at a time.
  let grid = $state(false);
  let nowrap = $state(false);
  let frame = $state<Frame>('none');
  let codeLang = $state<CodeLang>('javascript');
  let canvases: (HTMLCanvasElement | undefined)[] = $state([]);
  let missing: number[] = $state([]);
  let themeTick = $state(0);

  // Fixed defaults; explicit URL selections continue to take precedence.
  if (slots.length === 0) {
    slots = parse(['press-start-2p', 'pixelify-sans']);
  }
  if (!text) {
    const first = slots[0] ? bySlug.get(slots[0].slug) : undefined;
    text = first ? previewFor(first).text : defaultSample('latin');
  }

  onMount(() => onThemeChange(() => (themeTick += 1)));

  // Keep the URL in step so a comparison can be copied out of the address bar
  $effect(() => {
    const q = slots.map((x) => `${x.slug}:${x.variantId}`).join(',');
    const url = new URL(window.location.href);
    if (q) url.searchParams.set('v', q);
    else url.searchParams.delete('v');
    window.history.replaceState(null, '', url);
  });

  $effect(() => {
    const t = text;
    const z = zoom;
    // Read synchronously before the await, or Svelte can't track them and
    // ticking a checkbox wouldn't repaint
    const g = grid;
    const nw = nowrap;
    const fr = frame;
    const cl = codeLang;
    const list = slots.map((x) => ({ ...x }));
    void themeTick;
    let cancelled = false;
    (async () => {
      const { ink, paper } = framePalette(fr, themeInkPaper());
      const charColors = fr === 'code' ? highlightCode(t, cl) : undefined;
      const counts: number[] = [];
      for (const [i, slot] of list.entries()) {
        const el = canvases[i];
        if (!el || !t) continue;
        const [m, glyphs] = await Promise.all([
          store.loadFont(slot.slug, slot.variantId),
          store.glyphsFor(slot.slug, slot.variantId, t),
        ]);
        if (cancelled) return;
        const r = rasterize(t, glyphs, m, {
          invert: false,
          charColors,
          // No cap when wrapping is off: the column's canvas container scrolls
          // sideways rather than the page
          maxWidth: nw
            ? undefined
            : Math.max(48, Math.floor((el.parentElement?.clientWidth ?? 320) / z) - 2),
          ink,
          paper,
        });
        counts[i] = r.missing.length;
        paint(el, r, z, { grid: g });
      }
      missing = counts;
    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });

  function setSlug(i: number, slug: string) {
    const fam = bySlug.get(slug);
    if (!fam) return;
    slots[i] = { slug, variantId: previewFor(fam).variantId };
  }
  function add() {
    const used = new Set(slots.map((x) => x.slug));
    const next = sorted.find((f) => !used.has(f.slug)) ?? sorted[0];
    if (next) {
      slots = [...slots, { slug: next.slug, variantId: previewFor(next).variantId }];
    }
  }
  const remove = (i: number) => (slots = slots.filter((_, k) => k !== i));
</script>

<section id="compare" class="cmp" data-testid="compare">
  <div class="cmp__bar">
    <div class="cmp__presets">
      <span class="hint">{s.detail.presets}</span>
      {#each Object.entries(SAMPLES) as [langKey, sample] (langKey)}
        <button
          type="button"
          class="chip chipbtn"
          aria-pressed={text === sample}
          onclick={() => {
            text = sample;
            if (NOWRAP_PRESETS.has(langKey)) nowrap = true;
            if (langKey === 'javascript') {
              frame = 'code';
              codeLang = 'javascript';
            }
          }}>{presetLabel(langKey, s)}</button
        >
      {/each}
    </div>
    <button type="button" onclick={add} data-testid="compare-add"
      >{s.compare.add}</button
    >
  </div>

  <textarea
    name="compare-text"
    rows="2"
    bind:value={text}
    spellcheck="false"
    aria-label={s.detail.sampleTitle}
  ></textarea>

  <div class="cmp__controls">
    <label class="icon-control" title={s.catalogue.zoom}><Icon name="zoom-in" />
      <select name="compare-zoom" aria-label={s.catalogue.zoom} bind:value={zoom}>
        {#each [1, 2, 3, 4, 6, 8] as z (z)}<option value={z}>×{z}</option>{/each}
      </select>
    </label>
    <label class="check">
      <!-- Grid lines only render at ≥×4 (any smaller and they'd swallow the ink), so checking the box bumps the zoom up automatically -->
      <input
        type="checkbox"
        name="compare-grid"
        bind:checked={grid}
        onchange={() => {
          if (grid && zoom < 4) zoom = 4;
        }}
      />{s.catalogue.grid}
    </label>
    <label class="check"
      ><input type="checkbox" name="compare-nowrap" bind:checked={nowrap} />{s.catalogue
        .nowrap}</label
    >
    <FrameControls {s} bind:frame bind:codeLang />
  </div>

  <div class="cmp__grid">
    {#each slots as slot, i (i)}
      {@const fam = bySlug.get(slot.slug)}
      <div class="cmp__col">
        <div class="cmp__pick">
          <select
            name={`compare-font-${i + 1}`}
            value={slot.slug}
            onchange={(e) => setSlug(i, (e.currentTarget as HTMLSelectElement).value)}
            aria-label={s.compare.pickFont}
          >
            {#each sorted as f (f.slug)}<option value={f.slug}>{nameOf(f)}</option>{/each}
          </select>
          {#if fam && fam.variants.length > 1}
            {@const labels = variantLabels(fam.variants, s)}
            <select
              name={`compare-variant-${i + 1}`}
              bind:value={slots[i].variantId}
              aria-label={s.detail.variants}
            >
              {#each fam.variants as v, k (v.id)}<option value={v.id}>{labels[k]}</option>{/each}
            </select>
          {/if}
          {#if slots.length > 2}
            <button type="button" class="cmp__x" onclick={() => remove(i)} aria-label={s.compare.remove}
              >×</button
            >
          {/if}
        </div>
        <FrameShell {frame} {codeLang} dense>
          <canvas bind:this={canvases[i]}></canvas>
        </FrameShell>
        {#if (missing[i] ?? 0) > 0}
          <span class="chip chip--accent cmp__missing" data-testid="missing-count"
            >{s.detail.missingCount.replace('{n}', String(missing[i]))}</span
          >
        {/if}
        {#if fam}
          <a class="cmp__more" href={`${dataBase.replace(/\/data$/, '')}/${lang}/fonts/${fam.slug}/`}
            >{nameOf(fam)} →</a
          >
        {/if}
      </div>
    {/each}
  </div>
</section>

<style>
  .cmp__bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--s2) var(--s3);
    flex-wrap: wrap;
    margin-bottom: var(--s2);
  }
  .cmp__bar > * {
    min-width: 0;
    max-width: 100%;
  }
  .cmp__presets {
    display: flex;
    /* Language preset buttons don't fit on one row at 300px, so wrapping must be allowed */
    flex-wrap: wrap;
    gap: var(--s1);
    align-items: center;
  }
  .cmp__presets .hint {
    color: var(--ink-3);
    font-size: 0.75rem;
    margin-right: var(--s1);
  }
  .chipbtn {
    cursor: pointer;
    background: none;
  }
  .chipbtn[aria-pressed='true'] {
    color: var(--accent);
    border-color: var(--accent);
    background: var(--accent-soft);
  }
  textarea {
    width: 100%;
    resize: vertical;
    font-family: var(--font-ui);
  }
  .cmp__controls {
    display: flex;
    gap: var(--s4);
    align-items: center;
    flex-wrap: wrap;
    margin: var(--s2) 0 var(--s4);
    font-size: 0.85rem;
    color: var(--ink-2);
  }
  .check {
    display: flex;
    align-items: center;
    gap: var(--s1);
    cursor: pointer;
  }
  .cmp__missing {
    margin-top: var(--s2);
  }
  /* Side by side on a wide screen, stacked once the columns would get too
     narrow to judge a face by */
  .cmp__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(min(100%, 260px), 1fr));
    gap: var(--s4);
    align-items: start;
  }
  .cmp__col {
    min-width: 0;
    border: 1px solid var(--line);
    background: var(--surface);
    padding: var(--s3);
  }
  .cmp__pick {
    display: flex;
    gap: var(--s2);
    margin-bottom: var(--s2);
  }
  .cmp__pick select {
    min-width: 0;
    flex: 1 1 auto;
    font-size: 0.8rem;
  }
  .cmp__x {
    flex: none;
    padding: 0 var(--s2);
  }
  .cmp__more {
    display: inline-block;
    margin-top: var(--s2);
    font-size: 0.8rem;
  }
</style>
