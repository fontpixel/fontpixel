<script lang="ts">
  import { licenseShortLabel } from '../lib/licenselabel';
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import type { GlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import { previewFor } from '../lib/preview';
  import FixedSvg from './FixedSvg.svelte';
  import FrameShell from './FrameShell.svelte';
  import { framePalette, type Frame } from '../lib/frames';
  import { highlightCode, type CodeLang } from '../lib/codehl';
  import type { FamilyIndex } from '../lib/schema';
  import type { UIStrings } from '../i18n/types';

  interface Props {
    family: FamilyIndex;
    displayName: string;
    lang: string;
    s: UIStrings;
    sampleText: string;
    zoom: number;
    frame?: Frame;
    codeLang?: CodeLang;
    nowrap?: boolean;
    store: GlyphStore;
    href: string;
    dataBase: string;
    initialSvg?: string;
    initialNameSvg?: string;
  }
  const { family, displayName, lang, s, sampleText, zoom, store, href, dataBase, initialSvg = '', initialNameSvg = '',
    frame = 'none', codeLang = 'javascript', nowrap = false }: Props = $props();

  const preview = $derived(previewFor(family));
  const previewSize = $derived(family.variants.find(v => v.id === preview.variantId)?.size ?? family.sizes[0] ?? 16);
  // The catalogue is a compact specimen. Large grids stay at native size;
  // smaller fonts retain the requested integer zoom without blurring pixels.
  const previewZoom = $derived(Math.max(1, Math.min(zoom, Math.floor(48 / previewSize))));
  const text = $derived(
    sampleText.trim() ? sampleText : preview.text,
  );
  // Plain, inverted and game defaults can reuse their small static SVG. Code
  // needs the canvas even for default text, to color individual characters.
  const useCanvas = $derived(Boolean(sampleText.trim()) || frame === 'code');
  const sizeLabel = $derived(
    family.sizes.length > 3
      ? `${family.sizes[0]}–${family.sizes[family.sizes.length - 1]}${s.card.px}`
      : family.sizes.map((sz) => `${sz}${s.card.px}`).join(' '),
  );

  let canvasEl: HTMLCanvasElement | undefined = $state();
  let sampleWidth = $state(0);
  let rootEl: HTMLElement | undefined = $state();
  let visible = $state(false);
  let seen = $state(false);
  let missing = $state(0);
  let themeTick = $state(0);

  onMount(() => {
    const io = new IntersectionObserver(
      (entries) => {
        visible = entries.some((e) => e.isIntersecting);
        if (visible) seen = true;
      },
      { rootMargin: '200px' },
    );
    if (rootEl) io.observe(rootEl);
    const off = onThemeChange(() => (themeTick += 1));
    return () => {
      io.disconnect();
      off();
    };
  });

  $effect(() => {
    if (!useCanvas) { missing = 0; return; }
    if (!visible || !canvasEl || !sampleWidth) return;
    const t = text;
    const z = previewZoom;
    const width = sampleWidth;
    const fr = frame;
    const cl = codeLang;
    const nw = nowrap;
    void themeTick;
    let cancelled = false;
    (async () => {
      const [m, glyphs] = await Promise.all([
        store.loadFont(family.slug, preview.variantId),
        store.glyphsFor(family.slug, preview.variantId, t),
      ]);
      if (cancelled || !canvasEl) return;
      const { ink, paper } = framePalette(fr, themeInkPaper());
      const r = rasterize(t, glyphs, m, {
        invert: false,
        maxWidth: nw ? undefined : Math.max(1, Math.floor(width / z)),
        charColors: fr === 'code' ? highlightCode(t, cl) : undefined,
        ink,
        paper,
      });
      missing = r.missing.length;
      paint(canvasEl, r, z);

    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });
</script>

<article class="card" bind:this={rootEl} data-slug={family.slug} data-variant-id={preview.variantId}>
  <a class="card__link" {href}>
    <header class="card__head">
      <h2 class="card__name" data-vt="name">{displayName}</h2>
      <span class="card__marks">
        {#if !family.curated}<span class="chip">{s.card.uncurated}</span>{/if}
        {#if missing > 0}
          <span class="chip chip--accent mono" data-testid="missing-chip"
            >{s.detail.missingCount.replace('{n}', String(missing))}</span
          >
        {/if}
      </span>
    </header>
    {#if (seen || initialNameSvg) && family.namePreviews[displayName]}
      <div class="card__namecanvas" aria-hidden="true">
        <FixedSvg url={`${dataBase}/${family.namePreviews[displayName]}`} scale={Math.min(zoom + 1, 3)} maxHeight={64} initialSvg={initialNameSvg} />
      </div>
    {/if}
    <!-- data-vt marks the parts that fly to the font page (lib/viewtransition.ts) -->
    <div data-vt="preview">
      <FrameShell {frame} {codeLang} compact canvasClass="card__sample">
        <div class="card__sample-content" bind:clientWidth={sampleWidth}>
          {#if useCanvas}
            <canvas bind:this={canvasEl} width="0" height="0" aria-hidden="true"></canvas>
          {:else if seen || initialSvg}
            <FixedSvg url={`${dataBase}/${family.cardPreview || preview.file}`} scale={previewZoom} {initialSvg} />
          {/if}
        </div>
      </FrameShell>
    </div>
    <p class="card__meta mono">
      <span>{sizeLabel}</span>
      {#if family.forms.length}<span class="card__sep" aria-hidden="true">·</span><span
          >{family.forms.map(form => s.forms[form] ?? form).join(' / ')}</span
        >{/if}
      <span class="card__sep" aria-hidden="true">·</span>
      <span>{family.glyphCount.toLocaleString()} {s.card.glyphs}</span>
      <span class="card__lic" class:card__lic--warn={!family.license.spdx}>
        {family.license.spdx
          ? licenseShortLabel(family.license.spdx)
          : s.card.licenseUnknown}
      </span>
    </p>
  </a>
</article>

<style>
  .card {
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
    /* Grid rows stretch every card to the tallest in its row; the link has to
       stretch with it, or the card's lower part isn't clickable. */
    display: flex;
    flex-direction: column;
  }
  .card:hover {
    border-color: var(--accent);
  }
  .card__link {
    display: block;
    flex: 1 1 auto;
    padding: var(--s4);
  }
  .card__head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: var(--s2);
    margin-bottom: var(--s2);
  }
  .card__name {
    font-size: 0.92rem;
    margin: 0;
    color: var(--ink-2);
    font-weight: 600;
    letter-spacing: 0.01em;
  }
  .card__marks {
    display: flex;
    gap: var(--s1);
    flex-shrink: 0;
  }
  .card__namecanvas {
    display: block;
    margin-bottom: var(--s2);
    max-width: 100%;
    max-height: 5rem;
    overflow: auto;
  }
  .card__meta {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--s2);
    margin: var(--s3) 0 0;
    font-size: 0.75rem;
    color: var(--ink-3);
  }
  .card__sep {
    color: var(--line);
  }
  .card__lic {
    margin-left: auto;
    color: var(--ink-3);
  }
  .card__lic--warn {
    color: var(--accent);
  }
</style>
