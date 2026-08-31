<script lang="ts">
  /** bdfparser 活代码编辑器（移植自原站 Docusaurus 的 jsx live 代码块）。
   *
   * 用户在文本框里写整段 <BDF …func={…}/>，这里解析出 func 与
   * fontfile/pixelcolors/size 三个属性并即时渲染。执行用户代码用
   * new Function——跟原站 react-live 一样跑在用户自己的浏览器里。
   */
  import { onMount } from 'svelte';
  // Svelte 保留 $ 前缀标识符，$Font 等只能经命名空间属性访问
  import * as bdflib from 'bdfparser';
  import fetchline from 'fetchline';

  const base = import.meta.env.BASE_URL as string;
  const DEFAULT_CODE = `<BDF func={
  (font, {Font, Glyph, Bitmap, $Font, $Glyph, $Bitmap}) => {
    return font.draw('Hello! άßç й的のةُक!', {linelimit: 300}).glow(1)
  }
}/>`;

  let code = $state(DEFAULT_CODE);
  let error = $state('');
  let running = $state(false);
  let canvasEl: HTMLCanvasElement | undefined = $state();

  // 字体按 URL 缓存，改代码不重新下载
  const fontCache = new Map<string, Promise<unknown>>();
  function loadFont(url: string) {
    let p = fontCache.get(url);
    if (!p) {
      p = new bdflib.Font().load_filelines(fetchline(url));
      fontCache.set(url, p);
    }
    return p;
  }

  /** 不管写的是本地文件名还是原站完整 URL，都落到本站 public/bdfparser_fonts/。 */
  function resolveFont(name: string | undefined): string {
    const file = (name ?? 'unifont-reduced.bdf').split('?')[0]!.replace(/\/+$/, '');
    if (/^https?:/.test(file) && !file.includes('bdfparser_fonts/')) return file;
    return `${base}bdfparser_fonts/${file.split('/').pop()}`;
  }

  function parse(src: string) {
    const fi = src.indexOf('func={');
    if (fi < 0) throw new Error('缺少 func={…} / missing func={…}');
    let depth = 0;
    let end = -1;
    for (let k = fi + 5; k < src.length; k++) {
      if (src[k] === '{') depth += 1;
      else if (src[k] === '}') {
        depth -= 1;
        if (depth === 0) {
          end = k;
          break;
        }
      }
    }
    if (end < 0) throw new Error('func={…} 花括号不配对 / unbalanced braces');
    const funcText = src.slice(fi + 6, end);
    const rest = src.slice(0, fi) + src.slice(end + 1);
    const fontfile = /fontfile='([^']+)'/.exec(rest)?.[1];
    const size = /size=\{(\d+)\}/.exec(rest)?.[1];
    const pc = /pixelcolors=\{(\{[\s\S]*?\})\}/.exec(rest)?.[1];
    return { funcText, fontfile, size: size ? Number(size) : 2, pixelcolorsText: pc };
  }

  let seq = 0;
  async function run() {
    const my = ++seq;
    running = true;
    try {
      const { funcText, fontfile, size, pixelcolorsText } = parse(code);
      const fn = new Function(`return (${funcText})`)() as (f: unknown, c: unknown) => any;
      const pixelcolors = pixelcolorsText
        ? (new Function(`return (${pixelcolorsText})`)() as Record<number, string | null>)
        : undefined;
      const font = await loadFont(resolveFont(fontfile));
      if (my !== seq) return; // 已被更新的一次运行取代
      const bitmap = fn(font, bdflib);
      if (bitmap && canvasEl) {
        canvasEl.width = bitmap.width();
        canvasEl.height = bitmap.height();
        canvasEl.style.width = `${bitmap.width() * size}px`;
        const ctx = canvasEl.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);
          bitmap.draw2canvas(ctx, pixelcolors);
        }
      }
      error = '';
    } catch (e) {
      if (my === seq) error = String(e);
    } finally {
      if (my === seq) running = false;
    }
  }

  let timer: ReturnType<typeof setTimeout> | undefined;
  function onInput() {
    clearTimeout(timer);
    timer = setTimeout(run, 400);
  }

  onMount(run);
</script>

<div class="bdfed">
  <textarea
    class="bdfed__code mono"
    bind:value={code}
    oninput={onInput}
    spellcheck="false"
    rows={Math.max(8, code.split('\n').length + 1)}
  ></textarea>
  <div class="bdfed__out">
    {#if error}
      <p class="bdfed__error mono">{error}</p>
    {/if}
    <canvas bind:this={canvasEl} class:bdfed--busy={running}></canvas>
  </div>
</div>

<style>
  .bdfed {
    border: 1px solid var(--line, #ccc);
  }
  .bdfed__code {
    display: block;
    width: 100%;
    box-sizing: border-box;
    border: 0;
    border-bottom: 1px solid var(--line, #ccc);
    background: #0d0d0d;
    color: #d4d4d4;
    padding: 0.75em;
    font-size: 0.85rem;
    line-height: 1.5;
    resize: vertical;
  }
  .bdfed__code:focus {
    outline: 2px solid var(--accent, #b5312f);
    outline-offset: -2px;
  }
  .bdfed__out {
    padding: 0.75em;
    overflow-x: auto;
  }
  canvas {
    image-rendering: pixelated;
    max-width: none;
  }
  .bdfed--busy {
    opacity: 0.5;
  }
  .bdfed__error {
    color: #b5312f;
    font-size: 0.8rem;
    white-space: pre-wrap;
  }
</style>
