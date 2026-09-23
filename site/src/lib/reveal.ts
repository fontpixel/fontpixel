/** Show or hide `el` (its `hidden` attribute) with its height and opacity
 *  easing in or out. Toggling again mid-animation reverses from wherever the
 *  box has got to. With reduced motion, or without the Web Animations API, the
 *  attribute just flips. */
export function setRevealed(el: HTMLElement, show: boolean, duration = 250): void {
  const running = el.getAnimations?.().filter((a) => a.id === 'opf-reveal') ?? [];
  if (
    typeof el.animate !== 'function' ||
    matchMedia('(prefers-reduced-motion: reduce)').matches
  ) {
    running.forEach((a) => a.cancel());
    el.hidden = !show;
    return;
  }
  // Start from the current on-screen state, which may be part-way through an animation.
  const from = el.hidden ? 0 : el.getBoundingClientRect().height;
  const fromOpacity = el.hidden ? '0' : getComputedStyle(el).opacity;
  running.forEach((a) => a.cancel());
  el.hidden = false;
  const to = show ? el.getBoundingClientRect().height : 0;
  const anim = el.animate(
    [
      { height: `${from}px`, opacity: fromOpacity, overflow: 'hidden' },
      { height: `${to}px`, opacity: show ? 1 : 0, overflow: 'hidden' },
    ],
    { duration, easing: 'ease', id: 'opf-reveal' },
  );
  if (!show) anim.onfinish = () => (el.hidden = true);
}
