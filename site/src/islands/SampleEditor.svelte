<script lang="ts">
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { GlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import { SAMPLES, defaultSample } from '../lib/samples';
  import type { UIStrings } from '../i18n/types';

  interface VariantInfo {
    id: string;
    size: number;
    weight: string;
    spacing: string;
    script: string | null;
  }
  interface Props {
    slug: string;
    variants: VariantInfo[];
    s: UIStrings;
    dataBase: string;
    sampleLang: string;
  }
  const { slug, variants, s, dataBase, sampleLang }: Props = $props();

  const store = new GlyphStore(dataBase);
  let variantId = $state(variants[0]!.id);
  let text = $state('');
  let zoom = $state(2);
  let invert = $state(false);
  let grid = $state(false);
  let highlight = $state(true);
  let missing = $state(0);
  let themeTick = $state(0);
  let canvasEl: HTMLCanvasElement | undefined = $state();
  let wrapEl: HTMLElement | undefined = $state();

  onMount(() => {
    text = defaultSample(sampleLang);
    return onThemeChange(() => (themeTick += 1));
  });

  function variantLabel(v: VariantInfo): string {
    const bits = [`${v.size}px`, s.weightNames[v.weight] ?? v.weight,
      s.spacingNames[v.spacing] ?? v.spacing];
    if (v.script) bits.push(v.script);
    return bits.join(' · ');
  }

  $effect(() => {
    document.dispatchEvent(
      new CustomEvent('fbf:variantchange', { detail: { id: variantId } }),
    );
  });

  $effect(() => {
    if (!canvasEl || !text) return;
    const vid = variantId;
    const t = text;
    const z = zoom;
    const inv = invert;
    const g = grid;
    const hl = highlight;
    void themeTick;
    let cancelled = false;
    (async () => {
      const [m, glyphs] = await Promise.all([
        store.loadManifest(slug, vid),
        store.glyphsFor(slug, vid, t),
      ]);
      if (cancelled || !canvasEl) return;
      const { ink, paper } = themeInkPaper();
      const r = rasterize(t, glyphs, m, {
        invert: inv,
        highlightMissing: hl,
        maxWidth: Math.max(48, Math.floor((wrapEl?.clientWidth ?? 640) / z) - 2),
        ink,
        paper,
      });
      missing = r.missing.length;
      paint(canvasEl, r, z, { grid: g });
    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });
</script>

<section class="ed" data-testid="sample-editor">
  <div class="ed__bar">
    <label class="ed__variant"
      >{s.detail.variants}
      <select bind:value={variantId} data-testid="variant-select">
        {#each variants as v (v.id)}
          <option value={v.id}>{variantLabel(v)}</option>
        {/each}
      </select>
    </label>
    <div class="ed__presets">
      <span class="hint">{s.detail.presets}</span>
      {#each Object.entries(SAMPLES) as [langKey, sample] (langKey)}
        <button
          type="button"
          class="chip chipbtn"
          onclick={() => (text = sample)}>{langKey}</button
        >
      {/each}
    </div>
  </div>

  <textarea rows="3" bind:value={text} spellcheck="false"></textarea>

  <div class="ed__controls mono">
    <label>{s.catalogue.zoom}
      <select bind:value={zoom}>
        <option value={1}>×1</option>
        <option value={2}>×2</option>
        <option value={3}>×3</option>
        <option value={4}>×4</option>
      </select>
    </label>
    <label class="check"><input type="checkbox" bind:checked={invert} />{s.catalogue.invert}</label>
    <label class="check"><input type="checkbox" bind:checked={grid} />{s.catalogue.grid}</label>
    <label class="check">
      <input type="checkbox" bind:checked={highlight} />{s.detail.highlightMissing}
    </label>
    {#if missing > 0}
      <span class="chip chip--accent" data-testid="missing-count"
        >{s.detail.missingCount.replace('{n}', String(missing))}</span
      >
    {/if}
  </div>

  <div class="ed__canvas lattice" bind:this={wrapEl}>
    <canvas bind:this={canvasEl}></canvas>
  </div>
</section>

<style>
  .ed__bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: var(--s3);
    flex-wrap: wrap;
    margin-bottom: var(--s2);
  }
  .ed__variant {
    font-size: 0.85rem;
    color: var(--ink-2);
  }
  .ed__presets {
    display: flex;
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
  textarea {
    width: 100%;
    resize: vertical;
    font-family: var(--font-ui);
  }
  .ed__controls {
    display: flex;
    gap: var(--s4);
    align-items: center;
    flex-wrap: wrap;
    margin: var(--s2) 0 var(--s3);
    font-size: 0.8rem;
    color: var(--ink-2);
  }
  .check {
    display: flex;
    align-items: center;
    gap: var(--s1);
    cursor: pointer;
  }
  .ed__canvas {
    border: 1px solid var(--line);
    background: var(--surface);
    padding: var(--s4);
    overflow-x: auto;
  }
  .ed__canvas canvas {
    display: block;
    image-rendering: pixelated;
  }
</style>
