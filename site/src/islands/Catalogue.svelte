<script lang="ts">
  import { onMount } from 'svelte';
  import { applyFilters, emptyState, type CharLookup } from '../lib/filters';
  import { decodeState, encodeState } from '../lib/urlstate';
  import { GlyphStore } from '../lib/glyphstore';
  import type { FamilyIndex } from '../lib/schema';
  import type { UIStrings } from '../i18n/types';
  import FilterPanel from './FilterPanel.svelte';
  import FontCard from './FontCard.svelte';

  interface Props {
    families: FamilyIndex[];
    lang: string;
    s: UIStrings;
    dataBase: string;
    fontsBase: string;
  }
  const { families, lang, s, dataBase, fontsBase }: Props = $props();

  const store = new GlyphStore(dataBase);
  let state = $state(emptyState());
  let sampleInput = $state('');
  let sampleText = $state('');
  let zoom = $state(2);
  let invert = $state(false);
  let charLookup = $state<CharLookup | undefined>(undefined);
  let mounted = $state(false);

  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    const v = sampleInput;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => (sampleText = v), 150);
  });

  onMount(() => {
    state = decodeState(new URLSearchParams(location.search));
    document.querySelector('[data-ssr-grid]')?.remove();
    mounted = true;
  });

  // Task 18 接线:chars 查字懒加载覆盖区间索引
  $effect(() => {
    if (!state.chars.trim() || charLookup) return;
    import('../lib/intervals')
      .then(async (m) => {
        const idx = await m.loadCoverageIndex(dataBase);
        charLookup = (slug, chars) => idx.covers(slug, chars);
      })
      .catch(() => {});
  });

  $effect(() => {
    if (!mounted) return;
    const qs = encodeState(state).toString();
    history.replaceState(null, '', qs ? `?${qs}` : location.pathname);
  });

  const results = $derived(applyFilters(families, state, charLookup));
</script>

<section class="cat" data-testid="catalogue-island">
  <div class="cat__toolbar">
    <input
      class="cat__search"
      type="search"
      placeholder={s.catalogue.searchPlaceholder}
      bind:value={state.q}
      data-testid="search-input"
    />
    <input
      class="cat__sample"
      type="text"
      placeholder={s.catalogue.samplePlaceholder}
      bind:value={sampleInput}
      data-testid="sample-input"
    />
    <div class="cat__controls mono">
      <label>{s.catalogue.zoom}
        <select bind:value={zoom} data-testid="zoom-select">
          <option value={1}>×1</option>
          <option value={2}>×2</option>
          <option value={3}>×3</option>
        </select>
      </label>
      <label class="check">
        <input type="checkbox" bind:checked={invert} data-testid="invert-toggle" />
        {s.catalogue.invert}
      </label>
      <label>{s.catalogue.sort}
        <select bind:value={state.sort} data-testid="sort-select">
          <option value="name">{s.catalogue.sortName}</option>
          <option value="size">{s.catalogue.sortSize}</option>
          <option value="glyphs">{s.catalogue.sortGlyphs}</option>
          <option value="added">{s.catalogue.sortAdded}</option>
        </select>
      </label>
    </div>
  </div>

  <div class="cat__body">
    <details class="cat__filters" open>
      <summary class="cat__filters-summary">{s.catalogue.filters}</summary>
      <FilterPanel {families} bind:state {s} {lang} />
    </details>
    <div class="cat__main">
      <p class="cat__results mono" data-testid="result-count">
        {s.catalogue.results.replace('{n}', String(results.length))}
      </p>
      {#if results.length === 0}
        <div class="cat__empty">
          <p>{s.catalogue.noResults}</p>
          <p class="hint">{s.catalogue.noResultsHint}</p>
        </div>
      {:else}
        <div class="cat__grid">
          {#each results as family (family.slug)}
            <FontCard
              {family}
              {lang}
              {s}
              sampleText={sampleText}
              {zoom}
              {invert}
              {store}
              href={`${fontsBase}${family.slug}/`}
            />
          {/each}
        </div>
      {/if}
    </div>
  </div>
</section>

<style>
  .cat__toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: var(--s3);
    align-items: center;
    margin-bottom: var(--s4);
  }
  .cat__search {
    flex: 1 1 14rem;
  }
  .cat__sample {
    flex: 2 1 20rem;
  }
  .cat__controls {
    display: flex;
    gap: var(--s3);
    align-items: center;
    font-size: 0.85rem;
    color: var(--ink-2);
  }
  .check {
    display: flex;
    align-items: center;
    gap: var(--s1);
    cursor: pointer;
  }
  .cat__body {
    display: grid;
    grid-template-columns: 15rem 1fr;
    gap: var(--s6);
    align-items: start;
  }
  .cat__results {
    color: var(--ink-3);
    font-size: 0.8rem;
    margin: 0 0 var(--s3);
  }
  .cat__grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(19rem, 1fr));
    gap: var(--s4);
  }
  .cat__empty {
    padding: var(--s7) 0;
    text-align: center;
    color: var(--ink-2);
  }
  .cat__empty .hint {
    color: var(--ink-3);
    font-size: 0.85rem;
  }
  .cat__filters-summary {
    display: none;
  }
  @media (max-width: 900px) {
    .cat__body {
      grid-template-columns: 1fr;
      gap: var(--s4);
    }
    .cat__filters {
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: var(--s2) var(--s3);
      background: var(--surface);
    }
    .cat__filters-summary {
      display: list-item;
      cursor: pointer;
      font-weight: 600;
      font-size: 0.9rem;
    }
    .cat__filters:not([open]) {
      padding-bottom: var(--s2);
    }
  }
</style>
