<script lang="ts">
  /** Marks which variants meet a filter or script label: a double check when all
   *  do, a check-and-cross listing the ones that do otherwise. Callers show it
   *  only for families with more than one variant. */
  import Icon from './Icon.svelte';
  import { variantLabels } from '../lib/variantlabel';
  import type { FamilyIndex } from '../lib/schema';
  import type { UIStrings } from '../i18n/types';

  let { variants, matched, s, size = 14 }: {
    variants: FamilyIndex['variants'];
    matched: readonly string[];
    s: UIStrings;
    size?: number;
  } = $props();

  const all = $derived(variants.every((v) => matched.includes(v.id)));
  const title = $derived.by(() => {
    if (all) return s.card.allVariants;
    const labels = variantLabels(variants, s);
    const names = variants.flatMap((v, i) => (matched.includes(v.id) ? [labels[i]!] : []));
    return s.card.someVariants.replace('{list}', names.join(', '));
  });
</script>

<span class="vmark" class:vmark--some={!all} {title} aria-label={title} role="img"
  data-testid="variant-mark" data-variant-mark={all ? 'all' : 'some'}
  ><Icon name={all ? 'check-check' : 'check-x'} {size} /></span>

<style>
  .vmark {
    display: inline-flex;
    align-items: center;
    vertical-align: -0.15em;
    color: var(--ink-3);
    cursor: help;
  }
  .vmark--some {
    color: var(--accent);
  }
</style>
