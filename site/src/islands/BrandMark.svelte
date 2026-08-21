<script lang="ts">
  import { onMount } from 'svelte';
  import { themeInkPaper, onThemeChange } from '../lib/colors';
  import { GlyphStore } from '../lib/glyphstore';
  import { paint, rasterize } from '../lib/render';

  interface Props {
    slug: string;
    variantId: string;
    dataBase: string;
    text: string;
  }
  const { slug, variantId, dataBase, text }: Props = $props();

  let canvasEl: HTMLCanvasElement | undefined = $state();
  let ready = $state(false);
  let themeTick = $state(0);

  onMount(() => onThemeChange(() => (themeTick += 1)));

  $effect(() => {
    if (!canvasEl) return;
    void themeTick;
    const store = new GlyphStore(dataBase);
    let cancelled = false;
    (async () => {
      const [m, glyphs] = await Promise.all([
        store.loadManifest(slug, variantId),
        store.glyphsFor(slug, variantId, text),
      ]);
      if (cancelled || !canvasEl) return;
      if ([...text].some((ch) => !glyphs.get(ch.codePointAt(0)!))) return; // 缺字则保留文字版
      const { ink, paper } = themeInkPaper();
      const r = rasterize(text, glyphs, m, {
        invert: false,
        highlightMissing: false,
        ink,
        paper: [paper[0]!, paper[1]!, paper[2]!, 0], // 透明底融入页头
      });
      paint(canvasEl, r, 2);
      ready = true;
    })().catch(() => {});
    return () => {
      cancelled = true;
    };
  });
</script>

<span class="brand" class:ready>
  <canvas bind:this={canvasEl} aria-hidden="true"></canvas>
  <span class="brand__text">{text}</span>
</span>

<style>
  .brand {
    display: inline-flex;
    align-items: baseline;
  }
  .brand canvas {
    display: none;
    image-rendering: pixelated;
    transform: translateY(0.12em);
  }
  .brand.ready canvas {
    display: inline-block;
  }
  .brand.ready .brand__text {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
  }
  .brand__text {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: 0.02em;
  }
</style>
