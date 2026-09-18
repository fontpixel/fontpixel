<script lang="ts">
  /** The canvas dressing for a frame: plain, negative, code-editor window or
   * retro-game dialog box.
   *
   * Shared by the detail page's type-test box and the comparison grid — a
   * comparison whose columns were dressed differently from the detail page
   * would be showing two variables at once.
   */
  import type { Snippet } from 'svelte';
  import { CODE_LANG_EXT, type CodeLang } from '../lib/codehl';
  import type { Frame } from '../lib/frames';

  interface Props {
    frame: Frame;
    codeLang: CodeLang;
    /** Filename in the code frame's titlebar; the extension follows codeLang */
    fileName?: string;
    /** Tighter padding for the comparison's narrow columns */
    dense?: boolean;
    /** Bounded, scrollable viewport for catalogue cards. */
    compact?: boolean;
    canvasClass?: string;
    /** The canvas container, exposed so a caller can measure it for wrap width */
    canvasEl?: HTMLElement;
    children: Snippet;
  }
  let {
    frame,
    codeLang,
    fileName = 'sample',
    dense = false,
    compact = false,
    canvasClass = '',
    canvasEl = $bindable(),
    children,
  }: Props = $props();
</script>

<div
  class="fr"
  class:fr--invert={frame === 'invert'}
  class:fr--code={frame === 'code'}
  class:fr--game={frame === 'game'}
>
  {#if frame === 'code'}
    <div class="fr__titlebar mono" aria-hidden="true">
      <span class="fr__title">{fileName}.{CODE_LANG_EXT[codeLang]}</span>
      <span class="fr__winbtns"><span>–</span><span>□</span><span>×</span></span>
    </div>
  {/if}
  <div class={`fr__canvas lattice ${canvasClass}`} class:fr__canvas--dense={dense}
    class:fr__canvas--compact={compact} bind:this={canvasEl}>
    {@render children()}
  </div>
  {#if frame === 'game'}<div class="fr__crt" aria-hidden="true"></div>{/if}
</div>

<style>
  .fr { min-width: 0; }
  .fr__canvas {
    border: 1px solid var(--line);
    background: var(--surface);
    padding: var(--s4);
    overflow-x: auto;
  }
  .fr__canvas--dense {
    padding: var(--s2);
    min-height: 3rem;
  }
  .fr__canvas--compact {
    min-height: 3.6rem;
    max-height: 12rem;
    overflow: auto;
    padding: var(--s3);
    border-color: var(--line-soft);
  }
  /* The canvas itself is authored by the caller, so it falls under the
     caller's style scope, not this component's */
  .fr__canvas :global(canvas) {
    display: block;
    image-rendering: pixelated;
  }
  /* —— Invert: the whole canvas container (paper texture and padding included) turns negative together —— */
  .fr--invert .fr__canvas {
    filter: invert(1);
  }
  /* —— Code editor frame: black background, white text, regardless of light/dark theme —— */
  .fr--code .fr__titlebar {
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
  .fr__title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .fr__winbtns {
    margin-left: auto;
    display: inline-flex;
    gap: 12px;
  }
  .fr--code .fr__canvas {
    background: #0d0d0d;
    border-color: #000;
  }
  /* —— Retro-game dialog box: dark-navy background, gold double-line border, plus CRT scanlines —— */
  .fr--game {
    position: relative;
  }
  .fr--game .fr__canvas {
    background: #131353;
    color: #f0f0fc;
    border: 2px solid #efe2b0;
    border-radius: 8px;
    box-shadow:
      inset 0 0 0 2px #131353,
      inset 0 0 0 4px #8a7a45,
      0 0 0 3px #08061f;
  }
  .fr__crt {
    position: absolute;
    inset: 0;
    pointer-events: none;
    border-radius: 8px;
    background:
      repeating-linear-gradient(0deg, rgba(4, 2, 24, 0.22) 0 1px, transparent 1px 3px),
      radial-gradient(ellipse at center, rgba(0, 0, 0, 0) 60%, rgba(2, 0, 20, 0.38) 100%);
  }
</style>
