<script lang="ts">
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import type { GlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import { defaultSample } from '../lib/samples';
  import type { FamilyIndex } from '../lib/schema';
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
    lang === 'zh' && family.nameZh ? family.nameZh : family.name,
  );
  const variant = family.variants.reduce((a, b) => (b.glyphs > a.glyphs ? b : a));
  const text = $derived(sampleText.trim() || defaultSample(family.sampleLang));

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
        highlightMissing: true,
        maxWidth: Math.max(48, Math.floor((canvasEl.parentElement?.clientWidth ?? 320) / z)),
        ink,
        paper,
      });
      missing = r.missing.length;
      paint(canvasEl, r, z);

      // 家族名自渲染:仅当该字体覆盖名称全部字符
      if (nameEl) {
        const nameGlyphs = await store.glyphsFor(family.slug, variant.id, displayName);
        if (cancelled || !nameEl) return;
        const anyMissing = [...displayName].some(
          (ch) => !nameGlyphs.get(ch.codePointAt(0)!),
        );
        if (!anyMissing) {
          const nr = rasterize(displayName, nameGlyphs, m, {
            invert: inv,
            highlightMissing: false,
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
    <h2 class="card__name">{displayName}</h2>
    <canvas class="card__namecanvas" bind:this={nameEl} style="display:none" aria-hidden="true"
    ></canvas>
    <div class="card__sample">
      <canvas bind:this={canvasEl} aria-label={text}></canvas>
    </div>
    <p class="card__meta">
      {#each family.sizes as sz (sz)}
        <span class="chip mono">{sz}{s.card.px}</span>
      {/each}
      {#if family.form}<span class="chip">{s.forms[family.form] ?? family.form}</span>{/if}
      {#if family.license.spdx}
        <span class="chip">{family.license.spdx}</span>
      {:else}
        <span class="chip chip--accent">{s.card.licenseUnknown}</span>
      {/if}
      {#each family.scripts as sc (sc)}
        <span class="chip">{s.scriptNames[sc] ?? sc}</span>
      {/each}
      {#if family.converted}<span class="chip chip--accent">{s.card.converted}</span>{/if}
      {#if !family.curated}<span class="chip">{s.card.uncurated}</span>{/if}
      <span class="chip mono">{family.glyphCount.toLocaleString()} {s.card.glyphs}</span>
      {#if missing > 0}
        <span class="chip chip--accent mono" data-testid="missing-chip"
          >{s.detail.missingCount.replace('{n}', String(missing))}</span
        >
      {/if}
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
    border-color: var(--ink-3);
  }
  .card__link {
    display: block;
    padding: var(--s4);
  }
  .card__name {
    font-size: 1rem;
    margin: 0 0 var(--s2);
    color: var(--ink-2);
    font-weight: 600;
  }
  .card__namecanvas {
    display: block;
    margin-bottom: var(--s2);
    max-width: 100%;
  }
  .card__sample {
    min-height: 3rem;
    overflow: hidden;
  }
  .card__sample canvas {
    max-width: 100%;
    image-rendering: pixelated;
  }
  .card__meta {
    display: flex;
    flex-wrap: wrap;
    gap: var(--s1);
    margin: var(--s3) 0 0;
  }
</style>
