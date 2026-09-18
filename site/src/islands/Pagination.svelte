<script lang="ts">
  import { tick } from 'svelte';
  import { pageItems } from '../lib/catalogue';
  import type { UIStrings } from '../i18n/types';
  import Icon from './Icon.svelte';
  const { page, pages, href, s, onNavigate, disabled = false }:
    { page: number; pages: number; href: (page: number) => string; s: UIStrings; onNavigate?: () => void; disabled?: boolean } = $props();
  let editing = $state(false);
  let targetPage = $state<number | undefined>();
  let nav = $state<HTMLElement | undefined>();

  function focusEditor(input: HTMLInputElement) {
    input.focus();
    input.select();
  }
  async function cancelEdit() {
    editing = false;
    await tick();
    nav?.querySelector<HTMLButtonElement>('.page-edit')?.focus();
  }
  function jump(event: SubmitEvent) {
    event.preventDefault();
    if (typeof targetPage !== 'number' || !Number.isInteger(targetPage) || targetPage < 1 || targetPage > pages) return;
    onNavigate?.();
    window.location.assign(href(targetPage));
  }
</script>

{#if pages > 1}
  <nav bind:this={nav} class="pagination mono" aria-label={s.catalogue.pagination} data-testid="pagination">
    {#if editing}
      <form class="page-editor" onsubmit={jump}>
        <input type="number" name="page" min="1" max={pages} step="1" required
          bind:value={targetPage} use:focusEditor
          title={s.catalogue.editPage} aria-label={s.catalogue.editPage}
          data-testid="page-input" style:width={`${Math.max(2, String(pages).length) + 3}ch`}
          onblur={() => { editing = false; }}
          onkeydown={(event) => {
            if (event.key === 'Escape') { event.preventDefault(); void cancelEdit(); }
          }} />
      </form>
    {:else}
      <button type="button" class="page-edit" data-testid="page-edit" {disabled}
        title={s.catalogue.editPage} aria-label={s.catalogue.editPage}
        onclick={() => { targetPage = page; editing = true; }}><Icon name="pencil" size={16} /></button>
    {/if}
    {#if page > 1}
      <a href={href(page - 1)} rel="prev" onclick={onNavigate} data-testid="page-prev"
        title={s.catalogue.previousPage} aria-label={s.catalogue.previousPage}><Icon name="chevron-left" /></a>
    {/if}
    {#each pageItems(page, pages) as item, i (i)}
      {#if item === 'gap'}
        <span class="gap" aria-hidden="true">…</span>
      {:else}
        <a href={href(item)} aria-label={s.catalogue.pageLabel.replace('{n}', String(item))}
          aria-current={item === page ? 'page' : undefined} data-page={item} onclick={onNavigate}>{item}</a>
      {/if}
    {/each}
    {#if page < pages}
      <a href={href(page + 1)} rel="next" onclick={onNavigate} data-testid="page-next"
        title={s.catalogue.nextPage} aria-label={s.catalogue.nextPage}><Icon name="chevron-right" /></a>
    {/if}
  </nav>
{/if}

<style>
  .pagination { display: flex; flex-wrap: wrap; align-items: center; gap: var(--s1); font-size: 0.8rem; }
  a, .page-edit { display: inline-flex; align-items: center; justify-content: center; min-width: 2rem; min-height: 2rem; padding: 0 var(--s2); border: 1px solid var(--line); border-radius: var(--radius); }
  a, .page-edit { color: var(--ink-2); text-decoration: none; }
  a:hover, .page-edit:hover { color: var(--accent); border-color: var(--accent); }
  a[aria-current="page"] { color: var(--paper); background: var(--ink); border-color: var(--ink); }
  .gap { color: var(--ink-3); padding: 0 var(--s1); }
  .page-editor { display: inline-flex; margin: 0; }
  .page-editor input { min-width: 3rem; height: 2rem; text-align: center; appearance: textfield; }
  .page-editor input::-webkit-inner-spin-button,
  .page-editor input::-webkit-outer-spin-button { appearance: none; margin: 0; }
</style>
