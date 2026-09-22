<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { applyFilters, emptyState, type CharLookup } from '../lib/filters';
  import { decodeState, encodeState } from '../lib/urlstate';
  import { PAGE_SIZE, pageCount, pagePath, type CatalogueLabels } from '../lib/catalogue';
  import { getGlyphStore } from '../lib/glyphstore';
  import { revealFragment } from '../lib/fragments';
  import { SAMPLES, NOWRAP_PRESETS, matchingPreset, presetLabel } from '../lib/samples';
  import { CODE_LANGS, type CodeLang } from '../lib/codehl';
  import { FRAMES, type Frame } from '../lib/frames';
  import type { FamilyIndex } from '../lib/schema';
  import type { UIStrings, Lang } from '../i18n/types';
  import FilterPanel from './FilterPanel.svelte';
  import FontCard from './FontCard.svelte';
  import Pagination from './Pagination.svelte';
  import FrameControls from './FrameControls.svelte';
  import Icon from './Icon.svelte';

  interface Props {
    families: FamilyIndex[];
    labels: CatalogueLabels;
    lang: Lang;
    s: UIStrings;
    dataBase: string;
    fontsBase: string;
    catalogueBase: string;
    initialPage: number;
    previewSvgs: Record<string, string>;
    namePreviewSvgs: Record<string, string>;
    charsetIds: string[];
    charsetNames: Record<string, { zh: string; en: string; section: string; total: number }>;
  }
  const { families, labels, lang, s, dataBase, fontsBase, catalogueBase, initialPage, previewSvgs, namePreviewSvgs, charsetIds, charsetNames }: Props =
    $props();

  const store = getGlyphStore(dataBase);
  let filters = $state(emptyState());
  let page = $state(untrack(() => initialPage));
  let previousQuery = '';
  let sampleInput = $state('');
  let sampleText = $state('');
  let zoom = $state(2);
  let frame = $state<Frame>('none');
  let codeLang = $state<CodeLang>('javascript');
  const selectedPreset = $derived(matchingPreset(sampleInput));
  const nowrap = $derived(NOWRAP_PRESETS.has(matchingPreset(sampleText)));
  let charLookup = $state<CharLookup | undefined>(undefined);
  let mounted = $state(false);
  let filtersEl: HTMLDetailsElement | undefined = $state();

  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    const v = sampleInput;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => (sampleText = v), 150);
  });

  onMount(() => {
    filters = decodeState(new URLSearchParams(location.search));
    previousQuery = encodeState(filters).toString();
    try {
      const view = JSON.parse(sessionStorage.getItem('opf-catalogue-view') ?? 'null');
      if (view && typeof view.text === 'string') sampleInput = view.text;
      if (view && [1, 2, 3].includes(view.zoom)) zoom = view.zoom;
      if (view && FRAMES.includes(view.frame)) frame = view.frame;
      if (view && CODE_LANGS.includes(view.codeLang)) codeLang = view.codeLang;
    } catch { /* Storage is optional; browsing still works without it. */ }
    // Hand the panel back to native <details> behaviour. Until now the head script's
    // `narrow` class has been hiding its contents with CSS while the element itself
    // stayed open: collapsing it here is visually identical, so nothing shifts, and
    // from this point the summary toggles it the ordinary way.
    const narrow = matchMedia('(max-width: 900px)');
    if (filtersEl && narrow.matches) filtersEl.open = false;
    // The desktop summary is hidden, so a panel collapsed on mobile must reopen
    // when the viewport grows or the search and filters would become unreachable.
    const revealDesktopFilters = () => {
      if (filtersEl && !narrow.matches) filtersEl.open = true;
    };
    narrow.addEventListener('change', revealDesktopFilters);
    document.documentElement.classList.remove('narrow');
    mounted = true;
    revealFragment();
    return () => narrow.removeEventListener('change', revealDesktopFilters);
  });

  // Task 18 wiring: lazy-load the coverage interval index for `chars` glyph lookup
  $effect(() => {
    if (!filters.chars.trim() || charLookup) return;
    import('../lib/intervals')
      .then(async (m) => {
        const idx = await m.loadCoverageIndex(dataBase);
        charLookup = (slug, chars) => idx.covers(slug, chars);
      })
      .catch(() => {});
  });

  $effect.pre(() => {
    if (!mounted) return;
    const qs = encodeState(filters).toString();
    if (qs !== previousQuery) {
      previousQuery = qs;
      page = 1;
    }
    page = Math.max(1, Math.min(page, pages));
    const path = pagePath(catalogueBase, page);
    history.replaceState(history.state, '', path + (qs ? `?${qs}` : '') + location.hash);
    // Filtering can return a later page to page 1 without a document navigation.
    // Keep language links and canonical metadata in step with that clean URL.
    document.querySelectorAll<HTMLAnchorElement | HTMLLinkElement>(
      'a[data-lang-link], link[rel="canonical"], link[rel="alternate"][hreflang]',
    ).forEach((link) => {
      const url = new URL(link.href);
      url.pathname = pagePath(url.pathname.replace(/page\/\d+\/?$/, ''), page);
      link.href = url.href;
    });
    const canonical = document.querySelector<HTMLLinkElement>('link[rel="canonical"]');
    document.querySelector('meta[property="og:url"]')?.setAttribute('content', canonical?.href ?? location.href);
    document.title = page === 1 ? s.siteName : `${s.siteName} · ${s.catalogue.pageLabel.replace('{n}', String(page))}`;
    for (const name of ['og:title', 'twitter:title']) {
      document.querySelector(`meta[property="${name}"], meta[name="${name}"]`)?.setAttribute('content', document.title);
    }
    document.querySelector('meta[name="robots"]')?.setAttribute('content',
      qs ? 'noindex, follow' : 'index, follow, max-image-preview:large');
    const structured = document.querySelector<HTMLScriptElement>('script[type="application/ld+json"]');
    if (structured && canonical) {
      const data = JSON.parse(structured.textContent ?? '{}');
      data.url = canonical.href;
      data.name = document.title;
      structured.textContent = JSON.stringify(data);
    }
  });

  const results = $derived(applyFilters(families, filters, charLookup, charsetIds));
  const pages = $derived(pageCount(results.length));
  const pageResults = $derived(results.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE));
  function pageHref(value: number): string {
    const query = encodeState(filters).toString();
    return pagePath(catalogueBase, value) + (query ? `?${query}` : '');
  }
  function rememberView() {
    try { sessionStorage.setItem('opf-catalogue-view', JSON.stringify({ text: sampleInput, zoom, frame, codeLang })); }
    catch { /* Storage is optional. */ }
  }
  function selectPreset(key: string) {
    const sample = key === '' ? '' : SAMPLES[key];
    if (sample === undefined) return;
    clearTimeout(debounceTimer);
    sampleInput = sample;
    sampleText = sample;
    if (key === 'javascript') {
      frame = 'code';
      codeLang = 'javascript';
    }
  }
</script>

<section id="catalogue" class="cat" data-testid="catalogue-island" data-ready={mounted}>
  <div class="cat__body">
    <div class="cat__sidebar">
      <div class="cat__search">
        <input
          type="search"
          name="catalogue-search"
          placeholder={s.catalogue.searchPlaceholder}
          aria-label={s.catalogue.searchLabel}
          title={s.catalogue.searchLabel}
          bind:value={filters.q}
          data-testid="search-input"
          disabled={!mounted}
        />
        <span class="cat__search-icon"><Icon name="search" size={18} /></span>
      </div>
      <details class="cat__filters" open bind:this={filtersEl} inert={!mounted}>
        <summary class="cat__filters-summary">{s.catalogue.filters}</summary>
        <fieldset class="cat__filter-fields" disabled={!mounted}>
          <FilterPanel {labels} {families} bind:filters {s} {lang} {charsetIds} {charsetNames} />
        </fieldset>
      </details>
    </div>
    <div class="cat__main">
      <div class="cat__toolbar">
        <div class="cat__sample-field">
          <textarea
            class="cat__sample"
            name="catalogue-sample"
            rows={Math.min(4, sampleInput.split('\n').length)}
            disabled={!mounted}
            placeholder={s.catalogue.samplePlaceholder}
            aria-label={s.catalogue.sampleLabel}
            spellcheck="false"
            bind:value={sampleInput}
            data-testid="sample-input"
          ></textarea>
          <select class="cat__preset" name="catalogue-preset" value={selectedPreset || (sampleInput ? '__custom' : '')}
            disabled={!mounted} aria-label={s.catalogue.preset} title={s.catalogue.preset}
            data-testid="preset-select" onchange={(e) => selectPreset(e.currentTarget.value)}>
            <!-- Custom text also displays "Preset", but needs a distinct value
                 so choosing the visible reset option still fires change. -->
            {#if sampleInput && !selectedPreset}
              <option value="__custom" hidden disabled>{s.catalogue.preset}</option>
            {/if}
            <option value="">{s.catalogue.preset}</option>
            {#each Object.keys(SAMPLES) as key (key)}
              <option value={key}>{presetLabel(key, s)}</option>
            {/each}
          </select>
        </div>
        <div class="cat__controls">
          <label class="icon-control" title={s.catalogue.zoom}><Icon name="zoom-in" />
            <select name="catalogue-zoom" aria-label={s.catalogue.zoom} bind:value={zoom} data-testid="zoom-select" disabled={!mounted}>
              <option value={1}>×1</option>
              <option value={2}>×2</option>
              <option value={3}>×3</option>
            </select>
          </label>
          <FrameControls {s} bind:frame bind:codeLang disabled={!mounted} />
        </div>
      </div>

      <div class="cat__pagebar">
        <div class="cat__results-controls">
          <p class="cat__results mono" data-testid="result-count" aria-live="polite">
            {s.catalogue.results.replace('{n}', String(results.length))}
            {#if results.length > 0}
              <span class="cat__range"> · {s.catalogue.showing.replace('{start}', String((page - 1) * PAGE_SIZE + 1)).replace('{end}', String(Math.min(page * PAGE_SIZE, results.length)))}</span>
            {/if}
          </p>
          <label class="cat__sort" title={s.catalogue.sort}><Icon name="arrow-down-narrow-wide" />
            <select name="catalogue-sort" aria-label={s.catalogue.sort} bind:value={filters.sort} data-testid="sort-select" disabled={!mounted}>
              <option value="rating">{s.catalogue.sortAuto}</option>
              <option value="rating-reverse">{s.catalogue.sortAutoReverse}</option>
              <option value="name">{s.catalogue.sortName}</option>
              <option value="name-reverse">{s.catalogue.sortNameReverse}</option>
              <option value="size">{s.catalogue.sortSize}</option>
              <option value="size-reverse">{s.catalogue.sortSizeReverse}</option>
              <option value="glyphs">{s.catalogue.sortGlyphs}</option>
              <option value="glyphs-reverse">{s.catalogue.sortGlyphsReverse}</option>
            </select>
          </label>
        </div>
        <Pagination {lang} position="top" {page} {pages} href={pageHref} {s} onNavigate={rememberView} disabled={!mounted} />
      </div>
      <div
        id="catalogue-results"
        class="cat__results-region"
        role="region"
        aria-label={s.catalogue.skipToResults}
        tabindex="-1"
        data-testid="catalogue-results"
      >
        {#if results.length === 0}
          <div class="cat__empty">
            <p>{s.catalogue.noResults}</p>
            <p class="hint">{s.catalogue.noResultsHint}</p>
          </div>
        {:else}
          <div class="cat__grid">
            {#each pageResults as family (family.slug)}
              <FontCard
                {family}
                displayName={labels.names[family.slug] ?? family.name}
                {lang}
                {s}
                sampleText={sampleText}
                {zoom}
                {frame}
                {codeLang}
                {nowrap}
                {store}
                {dataBase}
                initialSvg={previewSvgs[family.slug] ?? ''}
                initialNameSvg={namePreviewSvgs[family.slug] ?? ''}
                href={`${fontsBase}${family.slug}/`}
              />
            {/each}
          </div>
          <div class="cat__bottom"><Pagination {lang} position="bottom" {page} {pages} href={pageHref} {s} onNavigate={rememberView} disabled={!mounted} /></div>
        {/if}
      </div>
    </div>
  </div>
</section>

<style>
  .cat__results-controls {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--s2) var(--s4);
  }
  .cat__sidebar {
    min-width: 0;
  }
  .cat__search {
    position: relative;
    margin-bottom: var(--s3);
  }
  .cat__search input {
    width: 100%;
    min-width: 0;
    padding-inline-end: 2.25rem;
    font-size: 1rem;
  }
  .cat__search-icon {
    position: absolute;
    inset-inline-end: var(--s2);
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    color: var(--ink-3);
    pointer-events: none;
  }
  .cat__sort {
    display: inline-flex;
    align-items: center;
    gap: var(--s2);
    font-size: .85rem;
    color: var(--ink-2);
    min-width: 0;
    max-width: 100%;
  }
  .cat__sort select { min-width: 0; max-width: calc(100% - 28px); }
  :global(html:lang(zh)) .cat__results,
  :global(html:lang(ja)) .cat__results { text-autospace: no-autospace; }
  .cat__toolbar {
    display: flex;
    flex-wrap: wrap;
    gap: var(--s3);
    align-items: flex-start;
    margin-bottom: var(--s4);
  }
  .cat__sample-field {
    flex: 1 1 min(28rem, 100%);
    display: flex;
    min-width: 0;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
  }
  .cat__sample {
    flex: 1;
    width: 0;
    min-width: 0;
    border: 0;
    resize: vertical;
    font-family: var(--font-ui);
  }
  .cat__sample[rows='1'] {
    white-space: pre;
    overflow: hidden;
  }
  .cat__preset {
    width: clamp(7rem, 16vw, 11rem);
    max-width: 45%;
    min-width: 0;
    border: 0;
    border-left: 1px solid var(--line);
    background: transparent;
    font-size: .8rem;
    text-overflow: ellipsis;
  }
  .cat__controls {
    display: flex;
    flex-wrap: wrap;
    min-width: 0;
    max-width: 100%;
    gap: var(--s2) var(--s3);
    align-items: center;
    font-size: 0.85rem;
    color: var(--ink-2);
  }
  /* Let the language picker wrap independently of the style buttons. */
  .cat__controls :global(.frames) { display: contents; }
  .cat__body {
    display: grid;
    /* minmax(0,…) lifts the default min-width:auto floor on grid children,
       otherwise card content wider than its track would blow out the whole page */
    grid-template-columns: minmax(0, 15rem) minmax(0, 1fr);
    gap: var(--s6);
    align-items: start;
  }
  .cat__results {
    color: var(--ink-3);
    font-size: 0.8rem;
    margin: 0;
  }
  .cat__pagebar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--s3); margin-bottom: var(--s3); }
  .cat__bottom { margin-top: var(--s5); display: flex; justify-content: center; }
  .cat__results-region {
    scroll-margin-top: var(--s4);
  }
  .cat__results-region:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: var(--s2);
  }
  .cat__grid {
    display: grid;
    /* min() lets the floor track the viewport: at 300px, a fixed 19rem (304px) would blow out the grid */
    grid-template-columns: repeat(auto-fill, minmax(min(19rem, 100%), 1fr));
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
  .cat__filter-fields { border: 0; padding: 0; margin: 0; min-width: 0; }
  /* The panel ships closed and is revealed here rather than rendered with `open`
     and collapsed by script. The page is ~1.4MB of HTML and paints progressively,
     so any script that runs after the element has already missed the first paint:
     the panel appeared expanded, then collapsed, and everything below it jumped.
     That single shift was the whole page's CLS. Both properties are needed --
     browsers hide closed <details> content with display:none or, in newer Chrome,
     content-visibility:hidden. */
  /* The panel is rendered open so that it needs no script to be usable, but on a
     narrow screen it should start collapsed. Letting script collapse it after
     hydration is too late: the page is ~1.4MB of HTML and paints progressively, so
     the panel is already on screen and everything below it jumps. Instead the head
     script sets `narrow` before the body is parsed and this rule hides the contents
     from the very first paint; onMount then closes the element for real and drops
     the class, which looks identical and so shifts nothing.
     :global is required on the child -- it is FilterPanel's root and carries that
     component's scope class, not this one's. */
  :global(html.narrow) .cat__filters[open] > :global(:not(summary)) {
    display: none;
  }
  @media (max-width: 900px) {
    .cat__body {
      grid-template-columns: minmax(0, 1fr);
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
