<script lang="ts">
  /** bdfparser 文档里的活演示（移植自原站 BDF.js）。
   *
   * 原组件接收 func 属性——MDX 里内联真函数，靠 React 同树编译才行得通；
   * Astro 岛屿的属性必须可序列化，故改为演示注册表：MDX 写 demo 名，
   * 代码住在这里。加一个演示就在 DEMOS 里添一项。
   */
  import { onMount } from 'svelte';
  // Svelte 保留 $ 前缀标识符，$Font 等只能经命名空间属性访问
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
  <canvas bind:this={canvasEl}></canvas>
{/if}

<style>
  canvas {
    image-rendering: pixelated;
  }
  .bdf-error {
    color: #b5312f;
    font-size: 0.8rem;
  }
</style>
