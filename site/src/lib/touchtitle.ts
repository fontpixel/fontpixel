/**
 * Touch screens never show native `title` tooltips, and many of the site's are
 * the only place a detail lives (script rules, variant lists, coverage sources).
 * A long press on any element with a title shows it in a bubble instead.
 *
 * Android fires `contextmenu` for a long press; iOS Safari doesn't, so a timer
 * covers it. On titled elements the system long-press menu (and, via CSS, the
 * iOS callout and text selection) gives way to the bubble; the release that
 * ends the press doesn't count as a tap, so a titled link isn't followed.
 */

const HOLD_MS = 500;
const SLOP_PX = 10;
const MARGIN_PX = 8;

const titled = (target: EventTarget | null) =>
  target instanceof Element ? target.closest<HTMLElement | SVGElement>('[title]:not([title=""])') : null;

export function installTouchTitles(doc: Document = document): () => void {
  const win = doc.defaultView!;
  let timer: ReturnType<typeof setTimeout> | undefined;
  let start: { x: number; y: number } | null = null;
  let pressed: Element | null = null;
  let tip: HTMLElement | null = null;
  // The release that ends a long press would otherwise count as a tap.
  let swallowClick = false;

  const cancel = () => {
    clearTimeout(timer);
    timer = undefined;
    start = null;
  };
  const hide = () => {
    tip?.remove();
    tip = null;
  };
  const show = (el: Element) => {
    const text = el.getAttribute('title');
    if (!text) return;
    hide();
    tip = doc.createElement('div');
    tip.className = 'touch-title';
    tip.setAttribute('role', 'tooltip');
    tip.textContent = text;
    doc.body.append(tip);
    const anchor = el.getBoundingClientRect();
    const box = tip.getBoundingClientRect();
    const left = Math.max(MARGIN_PX, Math.min(
      anchor.left + anchor.width / 2 - box.width / 2,
      win.innerWidth - box.width - MARGIN_PX,
    ));
    const above = anchor.top - box.height - MARGIN_PX;
    tip.style.left = `${left}px`;
    tip.style.top = `${above >= MARGIN_PX ? above : anchor.bottom + MARGIN_PX}px`;
    swallowClick = true;
  };

  const onDown = (e: PointerEvent) => {
    hide();
    cancel();
    swallowClick = false;
    pressed = e.pointerType === 'mouse' ? null : titled(e.target);
    if (!pressed) return;
    start = { x: e.clientX, y: e.clientY };
    const el = pressed;
    timer = setTimeout(() => {
      timer = undefined;
      show(el);
    }, HOLD_MS);
  };
  const onMove = (e: PointerEvent) => {
    if (start && Math.hypot(e.clientX - start.x, e.clientY - start.y) > SLOP_PX) cancel();
  };
  const onMenu = (e: Event) => {
    // Only a touch long press, never a mouse right-click: `pressed` is set
    // for touch and pen presses alone.
    if (!pressed || titled(e.target) !== pressed) return;
    e.preventDefault();
    cancel();
    if (!tip) show(pressed);
  };
  const onClick = (e: MouseEvent) => {
    if (!swallowClick) return;
    swallowClick = false;
    e.preventDefault();
    e.stopPropagation();
  };

  const listeners: [EventTarget, string, EventListener, AddEventListenerOptions][] = [
    [doc, 'pointerdown', onDown as EventListener, { capture: true, passive: true }],
    [doc, 'pointermove', onMove as EventListener, { capture: true, passive: true }],
    [doc, 'pointerup', cancel, { capture: true, passive: true }],
    [doc, 'pointercancel', cancel, { capture: true, passive: true }],
    [doc, 'contextmenu', onMenu, { capture: true }],
    [doc, 'click', onClick as EventListener, { capture: true }],
    // A pan already ends the press with pointercancel; scrolling only moves
    // the page out from under a shown bubble. Inner scrollers don't count.
    [win, 'scroll', hide, { passive: true }],
    [win, 'resize', hide, { passive: true }],
  ];
  for (const [target, type, fn, opts] of listeners) target.addEventListener(type, fn, opts);
  return () => {
    for (const [target, type, fn, opts] of listeners) target.removeEventListener(type, fn, opts);
    cancel();
    hide();
  };
}
