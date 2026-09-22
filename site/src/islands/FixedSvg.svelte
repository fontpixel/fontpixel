<script module lang="ts">
  import { compactPreviewSvg } from '../lib/svg-preview';
  const cache = new Map<string, Promise<string>>();
  function load(url: string): Promise<string> {
    let pending = cache.get(url);
    if (!pending) {
      pending = fetch(url).then((r) => {
        if (!r.ok) throw new Error(`SVG ${url}: ${r.status}`);
        return r.text().then(compactPreviewSvg);
      });
      cache.set(url, pending);
      void pending.catch(() => cache.delete(url));
    }
    return pending;
  }
</script>

<script lang="ts">
  import { untrack } from 'svelte';
  const { url, scale = 2, initialSvg = '', maxHeight }: {
    url: string;
    scale?: number;
    initialSvg?: string;
    /** Reduce enlargement in compact previews, keeping native pixels intact. */
    maxHeight?: number;
  } = $props();
  let svg = $state(untrack(() => initialSvg));
  $effect(() => {
    const source = url;
    if (initialSvg) { svg = initialSvg; return; }
    svg = '';
    let cancelled = false;
    load(source).then((value) => { if (!cancelled) svg = value; }).catch(console.error);
    return () => { cancelled = true; };
  });
  const scaled = $derived.by(() => {
    const box = /viewBox="0 0 ([\d.]+) ([\d.]+)"/.exec(svg);
    if (!box) return svg;
    const height = Number(box[2]);
    const fittedScale = maxHeight && height > 0
      ? Math.max(1, Math.min(scale, Math.floor(maxHeight / height)))
      : scale;
    return svg.replace('<svg ', `<svg width="${Number(box[1]) * fittedScale}" height="${height * fittedScale}" `);
  });
</script>

<div class="fixed-svg" aria-hidden="true">{@html scaled}</div>

<style>
  .fixed-svg :global(svg) { display: block; }
</style>
