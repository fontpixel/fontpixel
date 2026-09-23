<script lang="ts">
  import Icon from './Icon.svelte';
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { getGlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import type { RasterResult } from '../lib/render';
  import type { DecodedGlyph } from '../lib/bitmap';
  import { toBdfText, toDotText } from '../lib/dotcopy';
  import { NOWRAP_PRESETS, SAMPLES, defaultSample, presetLabel } from '../lib/samples';
  import { fragmentTarget, revealFragment } from '../lib/fragments';
  import { highlightCode, type CodeLang } from '../lib/codehl';
  import { framePalette, type Frame } from '../lib/frames';
  import FrameControls from './FrameControls.svelte';
  import FrameShell from './FrameShell.svelte';
  import type { UIStrings } from '../i18n/types';
  import { variantLabels, type LabelledVariant } from '../lib/variantlabel';

  type VariantInfo = LabelledVariant;
  interface Props {
    slug: string;
    variants: VariantInfo[];
    s: UIStrings;
    dataBase: string;
    sampleLang: string;
    sampleText: string;
    previewVariant: string;
  }
  const { slug, variants, s, dataBase, sampleLang, sampleText, previewVariant }:
    Props = $props();

  const store = getGlyphStore(dataBase);
  // Shares the variant with the top preview, so both sections show the same font
  let variantId = $state(
    variants.some((v) => v.id === previewVariant)
      ? previewVariant
      : variants[0]!.id,
  );
  let text = $state('');
  let zoom = $state(2);
  let nowrap = $state(false);
  // Canvas appearance, pick one of four: none (follows theme) / whole-frame invert / code editor (black background + syntax highlighting) / retro-game dialog box
  let frame = $state<Frame>('none');
  let codeLang = $state<CodeLang>('javascript');
  let grid = $state(false);
  // All variants: the same text drawn once per variant, stacked and labelled,
  // including different sizes, weights and styles.
  // It reuses whatever is currently typed and the current frame, which beats
  // a fixed sentence, so it lives here rather than in a section of its own.
  let ladder = $state(false);
  let ladderEls: (HTMLCanvasElement | undefined)[] = $state([]);
  let missing = $state(0);
  let themeTick = $state(0);
  let canvasEl: HTMLCanvasElement | undefined = $state();
  // For "copy dot matrix": keep the last render result and glyphs around
  let lastRaster = $state<RasterResult | null>(null);
  let lastGlyphs = $state<Map<number, DecodedGlyph | null> | null>(null);
  let copied = $state('');
  let wrapEl: HTMLElement | undefined = $state();

  onMount(() => {
    text = sampleText || defaultSample(sampleLang);
    // The coverage section also has a variant dropdown; keep the two in sync both ways
    const onExternal = (e: Event) => {
      const id = (e as CustomEvent).detail?.id;
      if (id && id !== variantId && variants.some((v) => v.id === id)) {
        variantId = id;
      }
    };
    document.addEventListener('opf:variantchange', onExternal);
    // Coverage anchors can point into another variant's initially hidden panel.
    const onFragment = (behavior: ScrollBehavior) => {
      const panel = fragmentTarget()?.closest<HTMLElement>('[data-variant-panel]');
      if (!panel) return;
      const ids = (panel.dataset.variantPanel ?? '').split(' ');
      if (!ids.includes(variantId)) {
        variantId = ids.find((id) => variants.some((v) => v.id === id)) ?? variantId;
      }
      revealFragment(behavior);
    };
    const onHashChange = () => onFragment('auto');
    onFragment('instant');
    window.addEventListener('hashchange', onHashChange);
    const off = onThemeChange(() => (themeTick += 1));
    return () => {
      document.removeEventListener('opf:variantchange', onExternal);
      window.removeEventListener('hashchange', onHashChange);
      off();
    };
  });

  async function copy(kind: 'hash' | 'dots' | 'bdf' | 'image') {
    try {
      if (kind === 'image') {
        // A PNG is more useful as a file than on the clipboard: the usual reason
        // to want one is to drop it into a sprite sheet or an image editor.
        const blob = await new Promise<Blob | null>((res) =>
          canvasEl ? canvasEl.toBlob(res, 'image/png') : res(null),
        );
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${slug}-${variantId}.png`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        if (!lastRaster) return;
        const out =
          kind === 'bdf'
            ? toBdfText(text, lastGlyphs ?? new Map())
            : toDotText(lastRaster, kind === 'hash' ? '#' : '@');
        if (!out) return;
        await navigator.clipboard.writeText(out);
      }
      copied = kind;
      setTimeout(() => (copied = ''), 1600);
    } catch (e) {
      console.error(e);
    }
  }

  // Labels are computed across the whole variant set: only report dimensions that actually differ within the group, while keeping every pair distinguishable
  const labels = $derived(variantLabels(variants, s));

  $effect(() => {
    document.dispatchEvent(
      new CustomEvent('opf:variantchange', { detail: { id: variantId } }),
    );
  });

  $effect(() => {
    lastRaster = null;
    lastGlyphs = null;
    if (!canvasEl || !text) return;
    const vid = variantId;
    const t = text;
    const z = zoom;
    const g = grid;
    // Dependencies must be read synchronously before the await, otherwise Svelte can't track them and toggling the checkbox won't trigger a repaint
    const nw = nowrap;
    const fr = frame;
    const cl = codeLang;
    void themeTick;
    let cancelled = false;
    (async () => {
      const [m, glyphs] = await Promise.all([
        store.loadFont(slug, vid),
        store.glyphsFor(slug, vid, t),
      ]);
      if (cancelled || !canvasEl) return;
      const { ink, paper } = framePalette(fr, themeInkPaper());
      const r = rasterize(t, glyphs, m, {
        // Invert isn't done here: it's a CSS invert on the whole canvas container (including the paper texture)
        invert: false,
        charColors: fr === 'code' ? highlightCode(t, cl) : undefined,
        // No cap when wrapping is off: the canvas expands to fit the longest line,
        // handled by .ed__canvas's horizontal overflow-x scroll so the page itself never overflows.
        maxWidth: nw
          ? undefined
          : Math.max(48, Math.floor((wrapEl?.clientWidth ?? 640) / z) - 2),
        ink,
        paper,
      });
      missing = r.missing.length;
      lastRaster = r;
      lastGlyphs = glyphs;
      paint(canvasEl, r, z, { grid: g });
    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });

  // One canvas per variant. Kept apart from the main render effect so toggling
  // the ladder never disturbs the single-variant preview.
  $effect(() => {
    if (!ladder || !text) return;
    const t = text;
    const z = zoom;
    const g = grid;
    const nw = nowrap;
    const fr = frame;
    const cl = codeLang;
    const width = wrapEl?.clientWidth ?? 640;
    void themeTick;
    let cancelled = false;
    (async () => {
      const { ink, paper } = framePalette(fr, themeInkPaper());
      for (const [i, v] of variants.entries()) {
        const el = ladderEls[i];
        if (!el) continue;
        const [m, glyphs] = await Promise.all([
          store.loadFont(slug, v.id),
          store.glyphsFor(slug, v.id, t),
        ]);
        if (cancelled) return;
        const r = rasterize(t, glyphs, m, {
          invert: false,
          charColors: fr === 'code' ? highlightCode(t, cl) : undefined,
          maxWidth: nw ? undefined : Math.max(48, Math.floor(width / z) - 2),
          ink,
          paper,
        });
        paint(el, r, z, { grid: g });
      }
    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });
</script>

<section id="sample-editor" class="ed" data-testid="sample-editor">
  <div class="ed__bar">
    <label class="ed__variant"
      >{s.detail.variants}
      <select name="sample-variant" bind:value={variantId} data-testid="variant-select">
        {#each variants as v, i (v.id)}
          <option value={v.id}>{labels[i]}</option>
        {/each}
      </select>
    </label>
    <div class="ed__presets">
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
          }}
          >{presetLabel(langKey, s)}</button
        >
      {/each}
    </div>
  </div>

  <textarea
    name="sample-text"
    rows="3"
    bind:value={text}
    spellcheck="false"
    aria-label={s.catalogue.sampleLabel}
  ></textarea>

  <div class="ed__controls">
    {#if variants.length > 1}
      <label class="ed__check"
        ><input
          type="checkbox"
          name="size-ladder"
          bind:checked={ladder}
          data-testid="ladder-toggle"
        />
        {s.detail.sizeLadder}</label
      >
    {/if}
    <label class="icon-control" title={s.catalogue.zoom}><Icon name="zoom-in" />
      <select name="sample-zoom" aria-label={s.catalogue.zoom} bind:value={zoom}>
        <option value={1}>×1</option>
        <option value={2}>×2</option>
        <option value={3}>×3</option>
        <option value={4}>×4</option>
      </select>
    </label>
    <label class="check">
      <!-- Grid lines only render at ≥×4 (any smaller and they'd swallow the ink), so checking the box bumps the zoom up automatically -->
      <input
        type="checkbox"
        name="sample-grid"
        bind:checked={grid}
        onchange={() => {
          if (grid && zoom < 4) zoom = 4;
        }}
      />{s.catalogue.grid}
    </label>
    <label class="check"
      ><input type="checkbox" name="sample-nowrap" bind:checked={nowrap} />{s.catalogue
        .nowrap}</label
    >
    {#if missing > 0}
      <span class="chip chip--accent" data-testid="missing-count"
        >{s.detail.missingCount.replace('{n}', String(missing))}</span
      >
    {/if}
    <FrameControls {s} bind:frame bind:codeLang />
  </div>

  <FrameShell {frame} {codeLang} bind:canvasEl={wrapEl}>
    {#if ladder}
      <div class="ed__ladder">
        {#each variants as v, i (v.id)}
          <div class="ed__rung">
            <span class="ed__rungname mono">{labels[i]}</span>
            <canvas bind:this={ladderEls[i]}></canvas>
          </div>
        {/each}
      </div>
    {:else}
      <canvas bind:this={canvasEl}></canvas>
    {/if}
  </FrameShell>

  <div class="ed__copy" data-testid="dot-copy">
    <span class="ed__copylabel">{s.detail.copyDots}</span>
    <button type="button" data-testid="copy-hash" disabled={ladder || !lastRaster} onclick={() => copy('hash')}
      >{copied === 'hash' ? s.detail.copied : '.#'}</button
    >
    <button type="button" data-testid="copy-dots" disabled={ladder || !lastRaster} onclick={() => copy('dots')}
      >{copied === 'dots' ? s.detail.copied : '.@'}</button
    >
    <button type="button" data-testid="copy-bdf" disabled={ladder || !lastRaster} onclick={() => copy('bdf')}
      >{copied === 'bdf' ? s.detail.copied : 'BDF'}</button
    >
    <button type="button" data-testid="copy-image" disabled={ladder || !lastRaster} onclick={() => copy('image')}
      >{copied === 'image' ? s.detail.saved : s.detail.savePng}</button
    >
  </div>
</section>

<style>
  .ed__ladder {
    display: flex;
    flex-direction: column;
    gap: var(--s4);
  }
  .ed__rung {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--s1);
  }
  .ed__rungname {
    font-size: 0.75rem;
    opacity: 0.6;
  }

  .ed {
    display: block;
    margin-bottom: var(--s6);
  }
  .ed__bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--s2) var(--s3);
    flex-wrap: wrap;
    margin-bottom: var(--s2);
  }
  /* Flex children default to min-width:auto; a long variant-dropdown label would blow out the toolbar */
  .ed__bar > * {
    min-width: 0;
    max-width: 100%;
  }
  .ed__bar select {
    max-width: 100%;
  }
  .ed__variant {
    font-size: 0.85rem;
    color: var(--ink-2);
  }
  .ed__presets {
    display: flex;
    /* Language preset buttons don't fit on one row at 300px, so wrapping must be allowed */
    flex-wrap: wrap;
    gap: var(--s1);
    align-items: center;
  }
  .ed__presets .hint {
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
  .ed__copy {
    display: flex;
    align-items: center;
    gap: var(--s2);
    margin-top: var(--s2);
    font-size: 0.85rem;
  }
  .ed__copylabel {
    color: var(--ink-3);
  }
  .ed__copy button {
    background: none;
    border: 1px solid var(--line);
    color: var(--ink-2);
    padding: 0 var(--s2);
    cursor: pointer;
  }
  .ed__copy button:hover {
    color: var(--accent);
    border-color: var(--accent);
  }
  .ed__copy button:disabled {
    opacity: 0.5;
    cursor: wait;
  }
  .ed__controls {
    display: flex;
    gap: var(--s4);
    align-items: center;
    flex-wrap: wrap;
    margin: var(--s2) 0 var(--s3);
    font-size: 0.85rem;
    color: var(--ink-2);
  }
  .check {
    display: flex;
    align-items: center;
    gap: var(--s1);
    cursor: pointer;
  }
</style>
