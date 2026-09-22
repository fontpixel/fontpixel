/**
 * Makes a set of controls a single stop in the page's Tab order. Focus stays
 * on one item at a time and the arrow, Home, and End keys move within the set.
 */
export function rovingFocus(node: HTMLElement) {
  const getItems = () =>
    [...node.querySelectorAll<HTMLElement>('button:not([disabled])')].filter(
      (item) => item.getAttribute('aria-disabled') !== 'true' && !item.hidden,
    );

  let current: HTMLElement | undefined;

  const setCurrent = (item: HTMLElement, focus = false) => {
    current = item;
    for (const candidate of getItems()) candidate.tabIndex = candidate === item ? 0 : -1;
    if (focus) item.focus();
  };

  const sync = () => {
    const items = getItems();
    if (!items.length) return;
    const next = current && items.includes(current)
      ? current
      : items.find((item) => item.getAttribute('aria-pressed') === 'true') ?? items[0]!;
    setCurrent(next);
  };

  const itemFromEvent = (event: Event) => {
    const target = event.target;
    return target instanceof Node ? getItems().find((item) => item.contains(target)) : undefined;
  };

  const rememberItem = (event: Event) => {
    const item = itemFromEvent(event);
    if (item) setCurrent(item);
  };

  const moveFocus = (event: KeyboardEvent) => {
    const item = itemFromEvent(event);
    if (!item) return;
    const items = getItems();
    const index = items.indexOf(item);
    let nextIndex: number | undefined;
    if (event.key === 'ArrowDown' || event.key === 'ArrowRight') {
      nextIndex = (index + 1) % items.length;
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowLeft') {
      nextIndex = (index - 1 + items.length) % items.length;
    } else if (event.key === 'Home') {
      nextIndex = 0;
    } else if (event.key === 'End') {
      nextIndex = items.length - 1;
    }
    if (nextIndex === undefined) return;
    event.preventDefault();
    setCurrent(items[nextIndex]!, true);
  };

  node.addEventListener('focusin', rememberItem);
  node.addEventListener('click', rememberItem);
  node.addEventListener('keydown', moveFocus);

  const observer = new MutationObserver(sync);
  observer.observe(node, {
    childList: true,
    subtree: true,
    attributes: true,
    attributeFilter: ['disabled', 'aria-disabled'],
  });
  sync();

  return {
    destroy() {
      observer.disconnect();
      node.removeEventListener('focusin', rememberItem);
      node.removeEventListener('click', rememberItem);
      node.removeEventListener('keydown', moveFocus);
    },
  };
}
