<script lang="ts">
  import type { FilterState } from '../lib/filters';
  import type { FamilyIndex } from '../lib/schema';
  import type { CatalogueLabels } from '../lib/catalogue';
  import type { UIStrings } from '../i18n/types';
  import { COVERAGE_PICKS } from '../lib/coveragepicks';
  import { licenseShortLabel } from '../lib/licenselabel';
  import { rovingFocus } from '../lib/roving-focus';
  import { VIBE_GROUPS, vibeGroupName } from '../lib/vibes';
  import Icon from './Icon.svelte';

  interface Props {
    families: FamilyIndex[];
    labels: CatalogueLabels;
    filters: FilterState;
    s: UIStrings;
    lang: string;
    charsetIds: string[];
    charsetNames: Record<string, { zh: string; en: string; section: string; total: number }>;
  }
  let { families, labels, filters = $bindable(), s, lang, charsetIds, charsetNames }: Props =
    $props();

  // Coverage filter: a single "charset ≥ percentage" rule, applied as soon as it changes
  let covId = $state('');
  // Pre-filled with 90%: the threshold used for the "script fully supported" judgment, and the most commonly asked-about number
  let covPct = $state<number | null>(90);
  let lastCoverageWrite: string | undefined;
  const csLabel = (id: string) =>
    labels.charsets[id] ?? id;
  // Listed in COVERAGE_PICKS order (Simplified → Traditional → Japanese → Korean → Latin), not alphabetically
  const csOptions = $derived(
    COVERAGE_PICKS.filter((id) => charsetNames[id] && charsetIds.includes(id)),
  );
  function applyCoverage() {
    const pct = covPct;
    const id = covId;
    const coverage = id && pct != null && pct > 0
      ? [{ id, min: Math.min(Math.max(pct, 0), 100) / 100 }]
      : [];
    lastCoverageWrite = JSON.stringify(coverage);
    filters.coverage = coverage;
  }
  $effect(() => {
    if (JSON.stringify(filters.coverage) === lastCoverageWrite) return;
    const req = filters.coverage[0];
    covId = req?.id ?? '';
    if (req) covPct = req.min * 100;
  });

  const uniq = <T,>(xs: T[]) => [...new Set(xs)];
  const forms = $derived(uniq(families.flatMap((f) => f.forms)).sort());
  const sizes = $derived(uniq(families.flatMap((f) => f.sizes)).sort((a, b) => a - b));
  const vibes = $derived(uniq(families.flatMap((f) => f.vibes)).sort());
  // Start selected groups open; subsequent expansion belongs to the user.
  let openVibeGroups = $state<Record<string, boolean>>({});
  const vibeGroups = $derived.by(() => {
    const groups = VIBE_GROUPS.map(group => ({ ...group, tags: group.tags.filter(tag => vibes.includes(tag)) })).filter(group => group.tags.length);
    const known = new Set(VIBE_GROUPS.flatMap(group => group.tags));
    const other = vibes.filter(tag => !known.has(tag));
    if (other.length) groups.push({ id: 'other', names: Array(5).fill(s.forms.other), tags: other });
    return groups;
  });
  // Scripts: fully-supported ones come first, "incomplete" ones come after, each group in a fixed order,
  // so the list order doesn't jump around as the number of included fonts changes
  const SCRIPT_ORDER = [
    'latin',
    'latin-supp',
    'latin-ext',
    'zh-hans',
    'zh-hant',
    'ja',
    'ko',
    'cyrillic',
    'greek',
    'arabic',
    'thai',
  ];
  const scriptRank = (sc: string) => {
    const partial = sc.endsWith('-partial');
    const base = partial ? sc.slice(0, -'-partial'.length) : sc;
    const i = SCRIPT_ORDER.indexOf(base);
    return (partial ? 100 : 0) + (i < 0 ? 99 : i);
  };
  const scripts = $derived(
    uniq(families.flatMap((f) => f.scripts)).sort((a, b) => scriptRank(a) - scriptRank(b)),
  );
  const licenses = $derived(
    uniq(families.map((f) => f.license.spdx ?? 'unknown')).sort(),
  );
  const weights = $derived(uniq(families.flatMap((f) => f.weights)).sort());
  const spacings = $derived(uniq(families.flatMap((f) => f.spacing)).sort());
  const inkRange = $derived.by(() => {
    const hs = families.map((f) => f.inkHeight).filter((h) => h > 0);
    return hs.length ? [Math.min(...hs), Math.max(...hs)] : [0, 0];
  });

  function toggle(list: string[], v: string): string[] {
    return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
  }
  function toggleNum(list: number[], v: number): number[] {
    return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
  }
  function reset() {
    covId = '';
    covPct = 90;
    const chars = filters.chars;
    const sort = filters.sort;
    filters = {
      q: '',
      forms: [],
      vibes: [],
      sizes: [],
      inkH: null,
      scripts: [],
      licenses: [],
      spacing: [],
      weights: [],
      coverage: [],
      chars,
      sort,
    };
  }
</script>

<aside id="filters" class="fp" data-testid="filter-panel">
  <div class="fp__head">
    <span class="fp__title">{s.catalogue.filters}</span>
    <button type="button" class="fp__reset" onclick={reset}
      title={s.catalogue.reset} aria-label={s.catalogue.reset}><Icon name="funnel-x" /></button>
  </div>

  <section id="filter-scripts">
    <h2>{s.catalogue.scripts}</h2>
    <div class="chips" role="toolbar" aria-label={s.catalogue.scripts} use:rovingFocus>
      {#each scripts as sc (sc)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={filters.scripts.includes(sc)}
          aria-pressed={filters.scripts.includes(sc)}
          title={s.scriptRules[sc] ?? ''}
          onclick={() => (filters.scripts = toggle(filters.scripts, sc))}
          >{s.scriptNames[sc] ?? sc}</button
        >
      {/each}
    </div>
  </section>

  <section id="filter-coverage">
    <h2>{s.catalogue.coveragePresets}</h2>
    <div class="cov" data-testid="coverage-filter">
      <select
        name="coverage-charset"
        value={covId}
        onchange={(e) => { covId = e.currentTarget.value; applyCoverage(); }}
        data-testid="coverage-charset"
        aria-label={s.catalogue.coveragePresets}
      >
        <option value="">{s.catalogue.coverageAny}</option>
        {#each csOptions as id (id)}
          <option value={id}>{csLabel(id)}</option>
        {/each}
      </select>
      <span class="cov__op mono">≥</span>
      <input
        class="cov__pct mono"
        type="number"
        name="coverage-pct"
        min="0"
        max="100"
        step="1"
        placeholder="90"
        data-testid="coverage-pct"
        value={covPct ?? ''}
        oninput={(e) => {
          const v = Number.parseFloat(e.currentTarget.value);
          covPct = Number.isFinite(v) ? v : null;
          applyCoverage();
        }}
      />
      <span class="cov__op mono">%</span>
      {#if covId}
        <button
          type="button"
          class="cov__clear"
          data-testid="coverage-clear"
          title={s.catalogue.coverageClear}
          onclick={() => { covId = ''; covPct = 90; applyCoverage(); }}>{s.catalogue.coverageClear}</button
        >
      {/if}
    </div>
  </section>

  <section id="filter-characters">
    <h2>{s.catalogue.charsLookup}</h2>
    <input
      type="text"
      name="filter-chars"
      placeholder={s.catalogue.charsPlaceholder}
      bind:value={filters.chars}
      data-testid="chars-input"
    />
    <p class="hint">{s.catalogue.charsHint}</p>
  </section>

  <section id="filter-sizes">
    <h2>{s.catalogue.sizes}</h2>
    <div class="chips" role="toolbar" aria-label={s.catalogue.sizes} use:rovingFocus>
      {#each sizes as sz (sz)}
        <button
          type="button"
          class="chip chipbtn mono"
          class:on={filters.sizes.includes(sz)}
          aria-pressed={filters.sizes.includes(sz)}
          data-size={sz}
          onclick={() => (filters.sizes = toggleNum(filters.sizes, sz))}
          >{sz}{s.card.px}</button
        >
      {/each}
    </div>
  </section>

  <section id="filter-ink-height">
    <h2>{s.catalogue.inkHeight}</h2>
    <div class="range mono">
      <input
        type="number"
        min={inkRange[0]}
        max={inkRange[1]}
        name="ink-height-min"
        placeholder={String(inkRange[0])}
        value={filters.inkH?.[0] ?? ''}
        oninput={(e) => {
          const v = Number.parseInt(e.currentTarget.value, 10);
          const hi = filters.inkH?.[1] ?? inkRange[1]!;
          filters.inkH = Number.isFinite(v) ? [v, hi] : null;
        }}
      />
      –
      <input
        type="number"
        min={inkRange[0]}
        max={inkRange[1]}
        name="ink-height-max"
        placeholder={String(inkRange[1])}
        value={filters.inkH?.[1] ?? ''}
        oninput={(e) => {
          const v = Number.parseInt(e.currentTarget.value, 10);
          const lo = filters.inkH?.[0] ?? inkRange[0]!;
          filters.inkH = Number.isFinite(v) ? [lo, v] : null;
        }}
      />
    </div>
  </section>

  <section id="filter-form">
    <h2>{s.catalogue.form}</h2>
    <div class="chips" role="toolbar" aria-label={s.catalogue.form} use:rovingFocus>
      {#each forms as f (f)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={filters.forms.includes(f)}
          aria-pressed={filters.forms.includes(f)}
          data-form={f}
          onclick={() => (filters.forms = toggle(filters.forms, f))}
          >{s.forms[f] ?? f}</button
        >
      {/each}
    </div>
  </section>

  <section id="filter-spacing-weight">
    <h2>{s.catalogue.spacing} · {s.catalogue.weights}</h2>
    <div
      class="chips"
      role="toolbar"
      aria-label={`${s.catalogue.spacing} · ${s.catalogue.weights}`}
      use:rovingFocus
    >
      {#each spacings as sp (sp)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={filters.spacing.includes(sp)}
          aria-pressed={filters.spacing.includes(sp)}
          onclick={() => (filters.spacing = toggle(filters.spacing, sp))}
          >{s.spacingNames[sp] ?? sp}</button
        >
      {/each}
      {#each weights as w (w)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={filters.weights.includes(w)}
          aria-pressed={filters.weights.includes(w)}
          onclick={() => (filters.weights = toggle(filters.weights, w))}
          >{s.weightNames[w] ?? w}</button
        >
      {/each}
    </div>
  </section>

  {#if vibes.length}
    <section id="filter-vibes">
      <h2>{s.catalogue.vibes}</h2>
      {#each vibeGroups as group (group.id)}
        <details
          class="vibe-group"
          open={openVibeGroups[group.id] ?? group.tags.some(tag => filters.vibes.includes(tag))}
          ontoggle={(event) => (openVibeGroups[group.id] = event.currentTarget.open)}
        >
          <summary>{vibeGroupName(group, lang)}</summary>
          <div class="chips">
            {#each group.tags as v (v)}
              <button
                type="button"
                class="chip chipbtn"
                class:on={filters.vibes.includes(v)}
                onclick={() => (filters.vibes = toggle(filters.vibes, v))}
                >{s.vibeNames[v] ?? v}</button
              >
            {/each}
          </div>
        </details>
      {/each}
    </section>
  {/if}

  <section id="filter-license">
    <h2>{s.catalogue.license}</h2>
    <div class="chips" role="toolbar" aria-label={s.catalogue.license} use:rovingFocus>
      {#each licenses as lic (lic)}
        <button
          type="button"
          class="chip chipbtn mono"
          class:on={filters.licenses.includes(lic)}
          aria-pressed={filters.licenses.includes(lic)}
          title={lic === 'unknown' ? s.card.licenseUnknown : (labels.licenses[lic] ?? lic)}
          onclick={() => (filters.licenses = toggle(filters.licenses, lic))}
          >{lic === 'unknown'
            ? s.card.licenseUnknown
            : licenseShortLabel(lic)}</button
        >
      {/each}
    </div>
  </section>

  </aside>

<style>
  .fp {
    font-size: 0.85rem;
  }
  .fp__head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--s2);
  }
  .fp__title {
    font-weight: 600;
  }
  .fp__reset {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 32px;
    min-height: 32px;
    border: none;
    color: var(--ink-3);
    font-size: 0.78rem;
    padding: 0;
  }
  .fp__reset:hover {
    color: var(--accent);
  }
  section {
    padding: var(--s3) 0;
    border-top: 1px dotted var(--line);
  }
  h2 {
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--ink-2);
    margin: 0 0 var(--s2);
    letter-spacing: 0.03em;
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: var(--s1);
  }
  .vibe-group + .vibe-group {
    margin-top: var(--s2);
  }
  .vibe-group summary {
    cursor: pointer;
    color: var(--ink-2);
    font-size: 0.78rem;
  }
  .vibe-group[open] summary {
    margin-bottom: var(--s2);
  }
  .chipbtn {
    cursor: pointer;
    background: none;
    /* Full license names can be long (e.g. WTFPL, CC BY-SA), so wrapping must be allowed or the panel clips them */
    max-width: 100%;
    white-space: normal;
    text-align: left;
  }
  .chipbtn.on {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-soft);
  }
  .hint {
    color: var(--ink-3);
    font-size: 0.75rem;
    margin: var(--s1) 0 0;
  }
  .range {
    display: flex;
    align-items: center;
    gap: var(--s2);
  }
  .range input {
    width: 4.5em;
  }
  .cov {
    display: flex;
    align-items: center;
    gap: var(--s1);
    flex-wrap: wrap;
  }
  .cov select {
    flex: 1 1 100%;
    min-width: 0;
    font-size: 0.78rem;
  }
  .cov__pct {
    width: 4em;
    flex: 0 0 auto;
  }
  .cov__op {
    color: var(--ink-3);
  }
  .cov__clear {
    border: none;
    color: var(--ink-3);
    font-size: 0.75rem;
    padding: 0 var(--s1);
  }
  .cov__clear:hover {
    color: var(--accent);
  }
  .check {
    display: flex;
    gap: var(--s2);
    align-items: center;
    margin-bottom: var(--s2);
    cursor: pointer;
  }
  input[type='text'] {
    width: 100%;
    min-width: 0;
  }
</style>
