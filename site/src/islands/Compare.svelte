<script lang="ts">
  /** Side-by-side comparison: the same text, the same pixel size, 2-4 faces.
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
  import { GlyphStore } from '../lib/glyphstore';
  import { rasterize, paint } from '../lib/render';
  import { themeInkPaper } from '../lib/colors';
  import { defaultSample } from '../lib/samples';
  import { variantLabels } from '../lib/variantlabel';

  interface Props {
    families: FamilyIndex[];
    s: UIStrings;
    dataBase: string;
    lang: string;
    /** slug:variantId pairs to preselect, from the page's query string */
    initial: string[];
  }
  const { families, s, dataBase, lang, initial }: Props = $props();

  const MAX = 4;
  const store = new GlyphStore(dataBase);
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
      const v = fam.variants.find((x) => x.id === vid) ?? fam.variants[0]!;
      out.push({ slug: fam.slug, variantId: v.id });
      if (out.length >= MAX) break;
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
  let canvases: (HTMLCanvasElement | undefined)[] = $state([]);
  let themeTick = $state(0);

  // Nothing chosen yet: open with two faces so the page is never a blank form
  if (slots.length === 0 && sorted.length >= 2) {
    slots = [
      { slug: sorted[0]!.slug, variantId: sorted[0]!.variants[0]!.id },
      { slug: sorted[1]!.slug, variantId: sorted[1]!.variants[0]!.id },
    ];
  }
  if (!text) {
    const first = slots[0] ? bySlug.get(slots[0].slug) : undefined;
    text = defaultSample(first?.sampleLang ?? 'latin');
  }

  onMount(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const bump = () => (themeTick += 1);
    mq.addEventListener('change', bump);
    const obs = new MutationObserver(bump);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    return () => {
      mq.removeEventListener('change', bump);
      obs.disconnect();
    };
  });

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
    const list = slots.map((x) => ({ ...x }));
    void themeTick;
    let cancelled = false;
    (async () => {
      const { ink, paper } = themeInkPaper();
      for (const [i, slot] of list.entries()) {
        const el = canvases[i];
        if (!el || !t) continue;
        const [m, glyphs] = await Promise.all([
          store.loadManifest(slot.slug, slot.variantId),
          store.glyphsFor(slot.slug, slot.variantId, t),
        ]);
        if (cancelled) return;
        const r = rasterize(t, glyphs, m, {
          invert: false,
          maxWidth: Math.max(48, Math.floor((el.parentElement?.clientWidth ?? 320) / z) - 2),
          ink,
          paper,
        });
        paint(el, r, z, {});
      }
    })().catch((e) => console.error(e));
    return () => {
      cancelled = true;
    };
  });

  function setSlug(i: number, slug: string) {
    const fam = bySlug.get(slug);
    if (!fam) return;
    slots[i] = { slug, variantId: fam.variants[0]!.id };
  }
  function add() {
    const used = new Set(slots.map((x) => x.slug));
    const next = sorted.find((f) => !used.has(f.slug)) ?? sorted[0];
    if (next && slots.length < MAX) {
      slots = [...slots, { slug: next.slug, variantId: next.variants[0]!.id }];
    }
  }
  const remove = (i: number) => (slots = slots.filter((_, k) => k !== i));
</script>

<section class="cmp" data-testid="compare">
  <div class="cmp__bar">
    <textarea rows="2" bind:value={text} spellcheck="false" aria-label={s.detail.sampleTitle}
    ></textarea>
    <label class="cmp__zoom"
      >{s.catalogue.zoom}
      <select bind:value={zoom}>
        {#each [1, 2, 3, 4, 6, 8] as z (z)}<option value={z}>×{z}</option>{/each}
      </select>
    </label>
    <button type="button" onclick={add} disabled={slots.length >= MAX} data-testid="compare-add"
      >{s.compare.add}</button
    >
  </div>

  <div class="cmp__grid">
    {#each slots as slot, i (i)}
      {@const fam = bySlug.get(slot.slug)}
      <div class="cmp__col">
        <div class="cmp__pick">
          <select
            value={slot.slug}
            onchange={(e) => setSlug(i, (e.currentTarget as HTMLSelectElement).value)}
            aria-label={s.compare.pickFont}
          >
            {#each sorted as f (f.slug)}<option value={f.slug}>{nameOf(f)}</option>{/each}
          </select>
          {#if fam && fam.variants.length > 1}
            {@const labels = variantLabels(fam.variants, s)}
            <select bind:value={slots[i].variantId} aria-label={s.detail.variants}>
              {#each fam.variants as v, k (v.id)}<option value={v.id}>{labels[k]}</option>{/each}
            </select>
          {/if}
          {#if slots.length > 2}
            <button type="button" class="cmp__x" onclick={() => remove(i)} aria-label={s.compare.remove}
              >×</button
            >
          {/if}
        </div>
        <div class="cmp__canvas lattice">
          <canvas bind:this={canvases[i]}></canvas>
        </div>
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
    align-items: flex-end;
    gap: var(--s3);
    flex-wrap: wrap;
    margin-bottom: var(--s4);
  }
  .cmp__bar textarea {
    flex: 1 1 20rem;
    min-width: 0;
  }
  .cmp__zoom {
    display: flex;
    align-items: center;
    gap: var(--s1);
    font-size: 0.85rem;
  }
  /* Side by side on a wide screen, stacked once the columns would get too
     narrow to judge a face by */
  .cmp__grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
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
  .cmp__canvas {
    overflow-x: auto;
    min-height: 3rem;
  }
  .cmp__more {
    display: inline-block;
    margin-top: var(--s2);
    font-size: 0.8rem;
  }
</style>
