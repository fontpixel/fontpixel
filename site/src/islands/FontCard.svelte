<script lang="ts">
  import { licenseShortLabel } from '../lib/licenselabel';
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import type { GlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import { defaultSample } from '../lib/samples';
  import type { FamilyIndex } from '../lib/schema';
  import { pickName, pickText } from '../i18n';
  import type { UIStrings } from '../i18n/types';

  interface Props {
    family: FamilyIndex;
    lang: string;
    s: UIStrings;
    sampleText: string;
    zoom: number;
    invert: boolean;
    store: GlyphStore;
    href: string;
  }
  const { family, lang, s, sampleText, zoom, invert, store, href }: Props = $props();

  const displayName = $derived(
    pickName(lang, family.names, family.name),
  );
  const variant = family.variants.reduce((a, b) => (b.glyphs > a.glyphs ? b : a));
  const text = $derived(
    sampleText.trim() || family.sampleText || defaultSample(family.sampleLang),
  );
  const sizeLabel = $derived(
    family.sizes.length > 3
      ? `${family.sizes[0]}–${family.sizes[family.sizes.length - 1]}${s.card.px}`
      : family.sizes.map((sz) => `${sz}${s.card.px}`).join(' '),
  );

  let canvasEl: HTMLCanvasElement | undefined = $state();
  let nameEl: HTMLCanvasElement | undefined = $state();
  let rootEl: HTMLElement | undefined = $state();
  let visible = $state(false);
  let missing = $state(0);
  let themeTick = $state(0);

  onMount(() => {
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          visible = true;
          io.disconnect();
        }
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
    if (!visible || !canvasEl) return;
    const t = text;
    const z = zoom;
    const inv = invert;
    void themeTick;
    let cancelled = false;
    (async () => {
      const [m, glyphs] = await Promise.all([
        store.loadManifest(family.slug, variant.id),
        store.glyphsFor(family.slug, variant.id, t),
      ]);
      if (cancelled || !canvasEl) return;
      const { ink, paper } = themeInkPaper();
      const r = rasterize(t, glyphs, m, {
        invert: inv,
        maxWidth: Math.max(48, Math.floor((canvasEl.parentElement?.clientWidth ?? 320) / z)),
        ink,
        paper,
      });
      missing = r.missing.length;
      paint(canvasEl, r, z);

      // 家族名自渲染：仅当该字体覆盖名称全部字符
      if (nameEl) {
        const nameGlyphs = await store.glyphsFor(family.slug, variant.id, displayName);
        if (cancelled || !nameEl) return;
        const anyMissing = [...displayName].some(
          (ch) => !nameGlyphs.get(ch.codePointAt(0)!),
        );
        if (!anyMissing) {
          const nr = rasterize(displayName, nameGlyphs, m, {
            invert: inv,
            ink,
            paper,
          });
          paint(nameEl, nr, Math.min(z + 1, 3));
          nameEl.style.display = '';
        } else {
          nameEl.style.display = 'none';
        }
      }
    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });
</script>

<article class="card" bind:this={rootEl} data-slug={family.slug}>
  <a class="card__link" {href}>
    <header class="card__head">
      <h2 class="card__name">{displayName}</h2>
      <span class="card__marks">
        {#if !family.curated}<span class="chip">{s.card.uncurated}</span>{/if}
        {#if missing > 0}
          <span class="chip chip--accent mono" data-testid="missing-chip"
            >{s.detail.missingCount.replace('{n}', String(missing))}</span
          >
        {/if}
      </span>
    </header>
    <canvas class="card__namecanvas" bind:this={nameEl} style="display:none" aria-hidden="true"
    ></canvas>
    <div class="card__sample lattice">
      <canvas bind:this={canvasEl} aria-hidden="true"></canvas>
    </div>
    <p class="card__meta mono">
      <span>{sizeLabel}</span>
      {#if family.form}<span class="card__sep">·</span><span
          >{s.forms[family.form] ?? family.form}</span
        >{/if}
      <span class="card__sep">·</span>
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
  }
  .card:hover {
    border-color: var(--accent);
  }
  .card__link {
    display: block;
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
  }
  .card__sample {
    min-height: 3.6rem;
    overflow: hidden;
    border: 1px solid var(--line-soft);
    padding: var(--s3);
  }
  .card__sample canvas {
    max-width: 100%;
    image-rendering: pixelated;
    display: block;
  }
  .card__meta {
    display: flex;
    flex-wrap: wrap;
    align-items: baseline;
    gap: var(--s2);
    margin: var(--s3) 0 0;
    font-size: 0.72rem;
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
