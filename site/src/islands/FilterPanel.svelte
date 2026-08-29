<script lang="ts">
  import type { FilterState } from '../lib/filters';
  import type { FamilyIndex } from '../lib/schema';
  import type { UIStrings } from '../i18n/types';

  interface Props {
    families: FamilyIndex[];
    state: FilterState;
    s: UIStrings;
    lang: string;
  }
  let { families, state = $bindable(), s, lang }: Props = $props();

  const uniq = <T,>(xs: T[]) => [...new Set(xs)];
  const forms = $derived(uniq(families.map((f) => f.form)).sort());
  const sizes = $derived(uniq(families.flatMap((f) => f.sizes)).sort((a, b) => a - b));
  const vibes = $derived(uniq(families.flatMap((f) => f.vibes)).sort());
  const scripts = $derived(uniq(families.flatMap((f) => f.scripts)));
  const licenses = $derived(
    uniq(families.map((f) => f.license.spdx ?? 'unknown')).sort(),
  );
  const weights = $derived(uniq(families.flatMap((f) => f.weights)).sort());
  const spacings = $derived(uniq(families.flatMap((f) => f.spacing)).sort());
  const inkRange = $derived.by(() => {
    const hs = families.map((f) => f.inkHeight).filter((h) => h > 0);
    return hs.length ? [Math.min(...hs), Math.max(...hs)] : [0, 0];
  });

  // 覆盖达标预设：官方标准名不译（引用），阈值见 spec §5.1
  const PRESETS: { key: string; zh: string; en: string; reqs: { id: string; min: number }[] }[] = [
    { key: 'gb2312', zh: 'GB/T 2312 ≥99%', en: 'GB/T 2312 ≥99%', reqs: [{ id: 'gb2312', min: 0.99 }] },
    { key: 'tgh', zh: '通用规范汉字表 ≥99%', en: 'General Standard ≥99%', reqs: [{ id: 'tongyong-guifan', min: 0.99 }] },
    { key: 'big5', zh: 'Big5 常用 ≥99%', en: 'Big5 frequent ≥99%', reqs: [{ id: 'big5-changyong', min: 0.99 }] },
    { key: 'tw4808', zh: '常用国字 ≥99%', en: 'TW common ≥99%', reqs: [{ id: 'tw-changyong-4808', min: 0.99 }] },
    { key: 'jis1', zh: 'JIS 第一水準 ≥99%', en: 'JIS level 1 ≥99%', reqs: [{ id: 'jisx0208-l1', min: 0.99 }] },
    { key: 'kana', zh: '假名 100%', en: 'Kana 100%', reqs: [{ id: 'hiragana', min: 1 }, { id: 'katakana', min: 1 }] },
    { key: 'ksx', zh: 'KS X 1001 谚文 ≥99%', en: 'KS X 1001 hangul ≥99%', reqs: [{ id: 'ksx1001-hangul', min: 0.99 }] },
    { key: 'wgl4', zh: 'WGL4 ≥99%', en: 'WGL4 ≥99%', reqs: [{ id: 'wgl4', min: 0.99 }] },
    { key: 'cp437', zh: 'CP437 ≥99%', en: 'CP437 ≥99%', reqs: [{ id: 'cp437', min: 0.99 }] },
  ];

  function toggle(list: string[], v: string): string[] {
    return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
  }
  function toggleNum(list: number[], v: number): number[] {
    return list.includes(v) ? list.filter((x) => x !== v) : [...list, v];
  }
  function presetActive(p: (typeof PRESETS)[number]): boolean {
    return p.reqs.every((r) =>
      state.coverage.some((c) => c.id === r.id && c.min === r.min),
    );
  }
  function togglePreset(p: (typeof PRESETS)[number]) {
    if (presetActive(p)) {
      state.coverage = state.coverage.filter(
        (c) => !p.reqs.some((r) => r.id === c.id && r.min === c.min),
      );
    } else {
      state.coverage = [
        ...state.coverage.filter((c) => !p.reqs.some((r) => r.id === c.id)),
        ...p.reqs,
      ];
    }
  }
  function reset() {
    const chars = state.chars;
    const q = state.q;
    const sort = state.sort;
    state = {
      q,
      forms: [],
      vibes: [],
      sizes: [],
      inkH: null,
      scripts: [],
      licenses: [],
      spacing: [],
      weights: [],
      origin: 'all',
      coverage: [],
      chars,
      sort,
    };
  }
</script>

<aside class="fp" data-testid="filter-panel">
  <div class="fp__head">
    <span class="fp__title">{s.catalogue.filters}</span>
    <button type="button" class="fp__reset" onclick={reset}>{s.catalogue.reset}</button>
  </div>

  <section>
    <h3>{s.catalogue.charsLookup}</h3>
    <input
      type="text"
      placeholder={s.catalogue.charsPlaceholder}
      bind:value={state.chars}
      data-testid="chars-input"
    />
    <p class="hint">{s.catalogue.charsHint}</p>
  </section>

  <section>
    <h3>{s.catalogue.form}</h3>
    <div class="chips">
      {#each forms as f (f)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={state.forms.includes(f)}
          data-form={f}
          onclick={() => (state.forms = toggle(state.forms, f))}
          >{s.forms[f] ?? f}</button
        >
      {/each}
    </div>
  </section>

  {#if vibes.length}
    <section>
      <h3>{s.catalogue.vibes}</h3>
      <div class="chips">
        {#each vibes as v (v)}
          <button
            type="button"
            class="chip chipbtn"
            class:on={state.vibes.includes(v)}
            onclick={() => (state.vibes = toggle(state.vibes, v))}>{v}</button
          >
        {/each}
      </div>
    </section>
  {/if}

  <section>
    <h3>{s.catalogue.sizes}</h3>
    <div class="chips">
      {#each sizes as sz (sz)}
        <button
          type="button"
          class="chip chipbtn mono"
          class:on={state.sizes.includes(sz)}
          data-size={sz}
          onclick={() => (state.sizes = toggleNum(state.sizes, sz))}
          >{sz}{s.card.px}</button
        >
      {/each}
    </div>
  </section>

  <section>
    <h3>{s.catalogue.inkHeight}</h3>
    <div class="range mono">
      <input
        type="number"
        min={inkRange[0]}
        max={inkRange[1]}
        placeholder={String(inkRange[0])}
        value={state.inkH?.[0] ?? ''}
        oninput={(e) => {
          const v = Number.parseInt(e.currentTarget.value, 10);
          const hi = state.inkH?.[1] ?? inkRange[1]!;
          state.inkH = Number.isFinite(v) ? [v, hi] : null;
        }}
      />
      –
      <input
        type="number"
        min={inkRange[0]}
        max={inkRange[1]}
        placeholder={String(inkRange[1])}
        value={state.inkH?.[1] ?? ''}
        oninput={(e) => {
          const v = Number.parseInt(e.currentTarget.value, 10);
          const lo = state.inkH?.[0] ?? inkRange[0]!;
          state.inkH = Number.isFinite(v) ? [lo, v] : null;
        }}
      />
    </div>
  </section>

  <section>
    <h3>{s.catalogue.scripts}</h3>
    <div class="chips">
      {#each scripts as sc (sc)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={state.scripts.includes(sc)}
          onclick={() => (state.scripts = toggle(state.scripts, sc))}
          >{s.scriptNames[sc] ?? sc}</button
        >
      {/each}
    </div>
  </section>

  <section>
    <h3>{s.catalogue.coveragePresets}</h3>
    <div class="chips">
      {#each PRESETS as p (p.key)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={presetActive(p)}
          onclick={() => togglePreset(p)}>{lang === 'zh' ? p.zh : p.en}</button
        >
      {/each}
    </div>
  </section>

  <section>
    <h3>{s.catalogue.license}</h3>
    <div class="chips">
      {#each licenses as lic (lic)}
        <button
          type="button"
          class="chip chipbtn mono"
          class:on={state.licenses.includes(lic)}
          onclick={() => (state.licenses = toggle(state.licenses, lic))}
          >{lic === 'unknown' ? s.card.licenseUnknown : lic}</button
        >
      {/each}
    </div>
  </section>

  <section>
    <h3>{s.catalogue.spacing} · {s.catalogue.weights}</h3>
    <div class="chips">
      {#each spacings as sp (sp)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={state.spacing.includes(sp)}
          onclick={() => (state.spacing = toggle(state.spacing, sp))}
          >{s.spacingNames[sp] ?? sp}</button
        >
      {/each}
      {#each weights as w (w)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={state.weights.includes(w)}
          onclick={() => (state.weights = toggle(state.weights, w))}
          >{s.weightNames[w] ?? w}</button
        >
      {/each}
    </div>
  </section>

  <section>
    <h3>{s.catalogue.origin}</h3>
    <div class="chips">
      {#each [['all', s.catalogue.originAll], ['native', s.catalogue.originNative], ['converted', s.catalogue.originConverted]] as [key, label] (key)}
        <button
          type="button"
          class="chip chipbtn"
          class:on={state.origin === key}
          onclick={() => (state.origin = key as FilterState['origin'])}>{label}</button
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
    align-items: baseline;
    margin-bottom: var(--s2);
  }
  .fp__title {
    font-weight: 600;
  }
  .fp__reset {
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
  h3 {
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
  .chipbtn {
    cursor: pointer;
    background: none;
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
  .check {
    display: flex;
    gap: var(--s2);
    align-items: center;
    margin-bottom: var(--s2);
    cursor: pointer;
  }
  input[type='text'] {
    width: 100%;
  }
</style>
