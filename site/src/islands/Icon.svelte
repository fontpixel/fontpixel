<script lang="ts">
  /** The Lucide outlines shared by catalogue and specimen controls. */
  const paths = {
    search: ['m21 21-4.34-4.34'],
    'funnel-x': ['M12.531 3H3a1 1 0 0 0-.742 1.67l7.225 7.989A2 2 0 0 1 10 14v6a1 1 0 0 0 .553.895l2 1A1 1 0 0 0 14 21v-7a2 2 0 0 1 .517-1.341l.427-.473', 'm16.5 3.5 5 5', 'm21.5 3.5-5 5'],
    'arrow-down-narrow-wide': ['m3 16 4 4 4-4', 'M7 20V4', 'M11 4h4', 'M11 8h7', 'M11 12h10'],
    'zoom-in': ['M21 21l-4.35-4.35', 'M11 8v6', 'M8 11h6'],
    'chevron-left': ['m15 18-6-6 6-6'],
    'chevron-right': ['m9 18 6-6-6-6'],
    'arrow-left': ['m12 19-7-7 7-7', 'M19 12H5'],
    'arrow-down': ['M12 5v14', 'm19 12-7 7-7-7'],
    pencil: ['M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z', 'm15 5 4 4'],
  };
  let { name, size = 20 }: { name: keyof typeof paths; size?: number } = $props();
</script>

<svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24"
  fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
  stroke-linejoin="round" class={`icon lucide lucide-${name}`} aria-hidden="true" focusable="false">
  {#each paths[name] as d}<path {d} />{/each}
  {#if name === 'search' || name === 'zoom-in'}<circle cx="11" cy="11" r="8" />{/if}
</svg>

<style>
  .icon { display: inline-block; flex-shrink: 0; vertical-align: middle; }
</style>
