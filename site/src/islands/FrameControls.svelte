<script lang="ts">
  /** The frame button group and code language picker, shared by all previews.
   * Labels are looked up through
   * FRAME_LABEL_KEY, which is typed against UIStrings, so a deleted string is a
   * build error rather than a button with nothing next to it. */
  import { CODE_LANGS, CODE_LANG_LABELS, type CodeLang } from '../lib/codehl';
  import { FRAMES, FRAME_LABEL_KEY, type Frame } from '../lib/frames';
  import type { UIStrings } from '../i18n/types';

  interface Props {
    s: UIStrings;
    frame: Frame;
    codeLang: CodeLang;
    disabled?: boolean;
  }
  let { s, frame = $bindable(), codeLang = $bindable(), disabled = false }: Props = $props();

  /* The id keeps the conditional language select's name unique when two
   * FrameControls are present on the same page. */
  const uid = $props.id();
</script>

<span class="frames" data-testid="frame-radios">
  <span class="frames__options" role="group" aria-label={s.catalogue.previewStyle}>
  {#each FRAMES as f (f)}
    {@const label = s.catalogue[FRAME_LABEL_KEY[f]]}
    <button
      type="button"
      class="frames__option"
      class:frames__option--selected={frame === f}
      class:frames__option--invert={f === 'invert'}
      aria-label={label}
      aria-pressed={frame === f}
      title={label}
      onclick={() => (frame = f)}
      {disabled}
    >
      {#if f === 'game'}
        <svg class="frames__icon frames__icon--game" viewBox="0 0 32 24" aria-hidden="true">
          <path d="M12 6V4.5C12 3 14 3 14 1" fill="none" stroke="#81768f" stroke-width="1.8" stroke-linecap="round" />
          <path d="M9 5h14c3 0 4.3 2.5 5 5.2l2 7.3c1 4-3 5.3-5.4 2.4L21 16H11l-3.6 3.9C5 22.8 1 21.5 2 17.5l2-7.3C4.7 7.5 6 5 9 5Z" fill="#9b8ad3" stroke="#534279" stroke-width="1.3" />
          <path d="M8 5.8h16c1.2 0 2.2 1 2.8 2.4H5.2C5.8 6.8 6.8 5.8 8 5.8Z" fill="#c5b8eb" />
          <path d="M8.5 8.5h3v3h3v3h-3v3h-3v-3h-3v-3h3Z" fill="#332d4e" />
          <circle cx="24" cy="10.5" r="2" fill="#ffcf62" stroke="#765423" stroke-width=".6" />
          <circle cx="20.5" cy="14" r="2" fill="#fb7c9d" stroke="#873e65" stroke-width=".6" />
          <path d="M15 15h2" stroke="#4b406b" stroke-width="1.5" stroke-linecap="round" />
        </svg>
      {:else if f === 'code'}
        <svg class="frames__icon" viewBox="0 0 28 24" fill="none" stroke="currentColor"
          stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="m8 6-6 6 6 6m12-12 6 6-6 6M16 4l-4 16" />
        </svg>
      {:else if f === 'invert'}
        <span class="frames__negative">{label}</span>
      {:else}
        <span>{label}</span>
      {/if}
    </button>
  {/each}
  </span>
  {#if frame === 'code'}
    <select class="frames__language" name={`${uid}-frame-lang`} bind:value={codeLang}
      aria-label={s.catalogue.codeLanguage} title={s.catalogue.codeLanguage} {disabled}>
      {#each CODE_LANGS as l (l)}<option value={l}>{CODE_LANG_LABELS[l]}</option>{/each}
    </select>
  {/if}
</span>

<style>
  .frames {
    display: inline-flex;
    align-items: center;
    /* On narrow screens (~300px) the four options don't fit on one row, so wrapping within the group must be allowed */
    flex-wrap: wrap;
    gap: var(--s2);
    min-width: 0;
    max-width: 100%;
    font-family: var(--font-ui);
  }
  .frames__options {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    padding: 2px;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
  }
  .frames__option {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-height: 30px;
    min-width: 34px;
    padding: 2px 6px;
    border: 1px solid transparent;
    border-radius: var(--radius);
    color: var(--ink-2);
    background: none;
    font-size: 0.8rem;
    line-height: 1.3;
    white-space: nowrap;
    cursor: pointer;
  }
  .frames__option:hover { background: var(--line-soft); }
  .frames__option--selected,
  .frames__option--selected:hover {
    color: var(--accent);
    border-color: var(--accent);
    background: var(--accent-soft);
  }
  .frames__option--invert { padding: 0; }
  /* Invert the same theme palette as the preview, leaving the selection border
     and keyboard focus ring outside the filter. */
  .frames__negative {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    align-self: stretch;
    min-height: 28px;
    min-width: 32px;
    padding: 2px 6px;
    border-radius: inherit;
    color: var(--canvas-ink);
    background: var(--canvas-paper);
    filter: invert(1);
  }
  .frames__option:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }
  .frames__option:disabled { opacity: .5; cursor: default; }
  .frames__icon { width: 25px; height: 22px; }
  .frames__icon--game { width: 29px; }
  .frames__language { min-width: 0; max-width: 100%; font-size: .8rem; }
</style>
