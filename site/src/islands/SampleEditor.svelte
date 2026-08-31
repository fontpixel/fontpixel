<script lang="ts">
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { GlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';
  import type { RasterResult } from '../lib/render';
  import type { DecodedGlyph } from '../lib/glyphpack';
  import { toBdfText, toDotText } from '../lib/dotcopy';
  import { NOWRAP_PRESETS, SAMPLES, defaultSample } from '../lib/samples';
  import {
    CODE_INK,
    CODE_LANGS,
    CODE_LANG_EXT,
    CODE_LANG_LABELS,
    CODE_PAPER,
    highlightCode,
    type CodeLang,
  } from '../lib/codehl';
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

  const store = new GlyphStore(dataBase);
  // 与顶部预览用同一个变体，上下两处才是同一份字体
  let variantId = $state(
    variants.some((v) => v.id === previewVariant)
      ? previewVariant
      : variants[0]!.id,
  );
  let text = $state('');
  let zoom = $state(2);
  let nowrap = $state(false);
  // 画布外观四选一：无（跟随主题）／整框反色／代码编辑器（黑底＋语法高亮）／老游戏对话框
  let frame = $state<'none' | 'invert' | 'code' | 'game'>('none');
  let codeLang = $state<CodeLang>('javascript');
  // 老游戏框：FF 式对话框的深藏青底、白字，与站点主题无关
  const GAME_PAPER = [19, 19, 83, 255] as const;
  const GAME_INK = [240, 240, 252, 255] as const;
  // 预设名优先用书写系统名；制表符、代码不是书写系统，另取标签
  const presetLabel = (k: string) =>
    s.scriptNames[k.toLowerCase()] ??
    (k === 'box-drawing' ? s.catalogue.boxDrawing : k === 'javascript' ? 'JavaScript' : k);
  let grid = $state(false);
  let missing = $state(0);
  let themeTick = $state(0);
  let canvasEl: HTMLCanvasElement | undefined = $state();
  // 供「复制点阵」用：留住最后一次渲染的结果与字形
  let lastRaster = $state<RasterResult | null>(null);
  let lastGlyphs = $state<Map<number, DecodedGlyph | null> | null>(null);
  let copied = $state('');
  let wrapEl: HTMLElement | undefined = $state();

  onMount(() => {
    text = sampleText || defaultSample(sampleLang);
    // 覆盖率那一段也有个变体下拉，两处双向同步
    const onExternal = (e: Event) => {
      const id = (e as CustomEvent).detail?.id;
      if (id && id !== variantId && variants.some((v) => v.id === id)) {
        variantId = id;
      }
    };
    document.addEventListener('opf:variantchange', onExternal);
    const off = onThemeChange(() => (themeTick += 1));
    return () => {
      document.removeEventListener('opf:variantchange', onExternal);
      off();
    };
  });

  async function copy(kind: 'dots' | 'bdf' | 'image') {
    try {
      if (kind === 'image') {
        const blob = await new Promise<Blob | null>((res) =>
          canvasEl ? canvasEl.toBlob(res, 'image/png') : res(null),
        );
        if (!blob) return;
        await navigator.clipboard.write([
          new ClipboardItem({ 'image/png': blob }),
        ]);
      } else {
        if (!lastRaster) return;
        const out =
          kind === 'dots'
            ? toDotText(lastRaster)
            : toBdfText(text, lastGlyphs ?? new Map());
        if (!out) return;
        await navigator.clipboard.writeText(out);
      }
      copied = kind;
      setTimeout(() => (copied = ''), 1600);
    } catch (e) {
      console.error(e);
    }
  }

  // 标签由整组变体一起算：只报组内真正有差异的维度，且保证两两可区分
  const labels = $derived(variantLabels(variants, s));

  $effect(() => {
    document.dispatchEvent(
      new CustomEvent('opf:variantchange', { detail: { id: variantId } }),
    );
  });

  $effect(() => {
    if (!canvasEl || !text) return;
    const vid = variantId;
    const t = text;
    const z = zoom;
    const g = grid;
    // 依赖必须在 await 之前同步读取，否则 Svelte 追踪不到，勾选后不会重画
    const nw = nowrap;
    const fr = frame;
    const cl = codeLang;
    void themeTick;
    let cancelled = false;
    (async () => {
      const [m, glyphs] = await Promise.all([
        store.loadManifest(slug, vid),
        store.glyphsFor(slug, vid, t),
      ]);
      if (cancelled || !canvasEl) return;
      const theme = themeInkPaper();
      const ink = fr === 'code' ? CODE_INK : fr === 'game' ? GAME_INK : theme.ink;
      const paper = fr === 'code' ? CODE_PAPER : fr === 'game' ? GAME_PAPER : theme.paper;
      const r = rasterize(t, glyphs, m, {
        // 反色不在这里做：它是整个画布容器（含衬纸纹理）的 CSS invert
        invert: false,
        charColors: fr === 'code' ? highlightCode(t, cl) : undefined,
        // 不换行时不给上限：画布按最长行撑开，由 .ed__canvas 的
        // overflow-x 横向滚动承接，页面本身不会溢出。
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
</script>

<section class="ed" data-testid="sample-editor">
  <div class="ed__bar">
    <label class="ed__variant"
      >{s.detail.variants}
      <select bind:value={variantId} data-testid="variant-select">
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
          onclick={() => {
            text = sample;
            if (NOWRAP_PRESETS.has(langKey)) nowrap = true;
            if (langKey === 'javascript') {
              frame = 'code';
              codeLang = 'javascript';
            }
          }}
          >{presetLabel(langKey)}</button
        >
      {/each}
    </div>
  </div>

  <textarea rows="3" bind:value={text} spellcheck="false"></textarea>

  <div class="ed__controls">
    <label>{s.catalogue.zoom}
      <select bind:value={zoom}>
        <option value={1}>×1</option>
        <option value={2}>×2</option>
        <option value={3}>×3</option>
        <option value={4}>×4</option>
      </select>
    </label>
    <label class="check">
      <!-- 网格线只有 ≥×4 才画得下（再小会吃掉墨迹），勾选时自动把缩放提上去 -->
      <input
        type="checkbox"
        bind:checked={grid}
        onchange={() => {
          if (grid && zoom < 4) zoom = 4;
        }}
      />{s.catalogue.grid}
    </label>
    <label class="check"><input type="checkbox" bind:checked={nowrap} />{s.catalogue.nowrap}</label>
    {#if missing > 0}
      <span class="chip chip--accent" data-testid="missing-count"
        >{s.detail.missingCount.replace('{n}', String(missing))}</span
      >
    {/if}
    <span class="ed__frames" data-testid="frame-radios">
      <label class="check"><input type="radio" bind:group={frame} value="none" />{s.catalogue.frameNone}</label>
      <label class="check"><input type="radio" bind:group={frame} value="invert" />{s.catalogue.invert}</label>
      <label class="check"><input type="radio" bind:group={frame} value="game" />{s.catalogue.frameGame}</label>
      <label class="check"><input type="radio" bind:group={frame} value="code" />{s.catalogue.frameCode}</label>
      {#if frame === 'code'}
        <select bind:value={codeLang} aria-label={s.catalogue.frameCode}>
          {#each CODE_LANGS as l (l)}
            <option value={l}>{CODE_LANG_LABELS[l]}</option>
          {/each}
        </select>
      {/if}
    </span>
  </div>

  <div
    class="ed__shell"
    class:ed__shell--invert={frame === 'invert'}
    class:ed__shell--code={frame === 'code'}
    class:ed__shell--game={frame === 'game'}
  >
    {#if frame === 'code'}
      <div class="ed__titlebar mono" aria-hidden="true">
        <span class="ed__title">sample.{CODE_LANG_EXT[codeLang]}</span>
        <span class="ed__winbtns"><span>–</span><span>□</span><span>×</span></span>
      </div>
    {/if}
    <div class="ed__canvas lattice" bind:this={wrapEl}>
      <canvas bind:this={canvasEl}></canvas>
    </div>
    {#if frame === 'game'}<div class="ed__crt" aria-hidden="true"></div>{/if}
  </div>

  <div class="ed__copy" data-testid="dot-copy">
    <span class="ed__copylabel">{s.detail.copyDots}</span>
    <button type="button" data-testid="copy-dots" onclick={() => copy('dots')}
      >{copied === 'dots' ? s.detail.copied : '.#'}</button
    >
    <button type="button" data-testid="copy-bdf" onclick={() => copy('bdf')}
      >{copied === 'bdf' ? s.detail.copied : 'BDF'}</button
    >
    <button type="button" data-testid="copy-image" onclick={() => copy('image')}
      >{copied === 'image' ? s.detail.copied : 'PNG'}</button
    >
  </div>
</section>

<style>
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
  /* flex 子项默认 min-width:auto，变体下拉的长标签会把工具条撑破 */
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
    /* 语言预设按钮在 300px 屏上排不下一行，必须允许折行 */
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
  /* —— 反色：整个画布容器（含衬纸纹理与内边距）一起底片化 —— */
  .ed__shell--invert .ed__canvas {
    filter: invert(1);
  }
  /* —— 代码编辑器外框：无论明暗主题都是黑底白字 —— */
  .ed__shell--code .ed__titlebar {
    display: flex;
    align-items: center;
    gap: var(--s2);
    background: #2b2b2b;
    color: #c9c9c9;
    border: 1px solid #000;
    border-bottom: none;
    border-radius: 6px 6px 0 0;
    padding: 4px 10px;
    font-size: 12px;
  }
  .ed__winbtns {
    margin-left: auto;
    display: inline-flex;
    gap: 12px;
  }
  .ed__shell--code .ed__canvas {
    background: #0d0d0d;
    border-color: #000;
  }
  /* —— 老游戏对话框：深藏青底、金色双线描边，外加 CRT 扫描线 —— */
  .ed__shell--game {
    position: relative;
  }
  .ed__shell--game .ed__canvas {
    background: #131353;
    border: 2px solid #efe2b0;
    border-radius: 8px;
    box-shadow:
      inset 0 0 0 2px #131353,
      inset 0 0 0 4px #8a7a45,
      0 0 0 3px #08061f;
  }
  .ed__crt {
    position: absolute;
    inset: 0;
    pointer-events: none;
    border-radius: 8px;
    background:
      repeating-linear-gradient(0deg, rgba(4, 2, 24, 0.22) 0 1px, transparent 1px 3px),
      radial-gradient(ellipse at center, rgba(0, 0, 0, 0) 60%, rgba(2, 0, 20, 0.38) 100%);
  }
  .ed__frames {
    display: inline-flex;
    align-items: center;
    /* 窄屏（300px 级）一行放不下四个选项，必须允许组内折行 */
    flex-wrap: wrap;
    gap: var(--s2);
    padding-left: var(--s3);
    border-left: 1px solid var(--line);
  }
</style>
