<script lang="ts">
  /** Live demo for the bdfparser docs (ported from the original site's BDF.js).
   *
   * The original component took a func prop — an inline real function in MDX,
   * which only worked because React compiled it in the same tree. Astro island
   * props must be serializable, so this uses a demo registry instead: MDX
   * writes the demo name, and the code lives here. Adding a demo means adding
   * an entry to DEMOS.
   */
  import { onMount } from 'svelte';
  // Svelte reserves $-prefixed identifiers, so $Font etc. can only be accessed via the namespace prop
  import * as bdflib from 'bdfparser';
  import fetchline from 'fetchline';

  import { DEMOS } from './bdfdemos.gen';

  interface Props {
    demo: string;
  }
  const base = import.meta.env.BASE_URL as string;
  let { demo }: Props = $props();
  const entry = DEMOS[demo];
  const size = entry?.size ?? 2;
  const pixelcolors = entry?.pixelcolors;
  const fontfile = `${base}bdfparser_fonts/${entry?.fontfile ?? 'unifont-reduced.bdf'}`;

  let canvasEl: HTMLCanvasElement | undefined = $state();
  let error = $state('');

  onMount(async () => {
    try {
      if (!entry) {
        error = `unknown demo: ${demo}`;
        return;
      }
      const font = await new bdflib.Font().load_filelines(fetchline(fontfile));
      const bitmap = entry.fn(font, bdflib);
      if (bitmap && canvasEl) {
        canvasEl.style.width = '100%';
        canvasEl.style.height = `${bitmap.height() * size}px`;
        canvasEl.width = canvasEl.offsetWidth / size;
        canvasEl.height = canvasEl.offsetHeight / size;
        const ctx = canvasEl.getContext('2d');
        if (ctx) bitmap.draw2canvas(ctx, pixelcolors);
      }
    } catch (e) {
      error = String(e);
    }
  });
</script>

{#if error}
  <p class="bdf-error mono">{error}</p>
{:else}
  <canvas bind:this={canvasEl} role="img" aria-label="Bitmap output for the accompanying code example"></canvas>
{/if}

<style>
  canvas {
    image-rendering: pixelated;
  }
  .bdf-error {
    color: var(--accent);
    font-size: 0.8rem;
  }
</style>
