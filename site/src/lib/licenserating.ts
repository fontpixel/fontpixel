/** Small catalogue preference for easier reuse, not a legal compatibility verdict. */
export function licenseFactor(spdx: string | null | undefined): number {
  if (!spdx?.trim()) return 1;
  const tokens = spdx.match(/[^\s()]+|[()]/g)!;
  let pos = 0;
  const take = (token: string) => tokens[pos] === token && (++pos > 0);
  const atom = (): number => {
    if (take('(')) {
      const value = either();
      if (!take(')')) throw new Error('Unclosed license expression');
      return value;
    }
    const id = tokens[pos++];
    if (!id || ['AND', 'OR', 'WITH', ')'].includes(id)) throw new Error('Missing license');
    const exception = take('WITH') ? tokens[pos++] : undefined;
    if (tokens[pos - 1] === 'WITH') throw new Error('Missing exception');
    if (/^(?:A?GPL)-\d/.test(id)) {
      const fontException = /-with-font-exception$/.test(id)
        || /^Font-exception-\d/.test(exception ?? '');
      return fontException ? 0.985 : 0.96;
    }
    if (/^CC-BY-SA-/.test(id)) return 0.98;
    // OFL has font-scoped copyleft but explicitly permits ordinary document and
    // app use. Keep it at baseline with permissive licences. Unknown/custom
    // licences stay neutral; this does not classify them as permissive.
    return 1;
  };
  const together = (): number => {
    let value = atom();
    // Both obligations apply: use the more restrictive rating, without stacking.
    while (take('AND')) value = Math.min(value, atom());
    return value;
  };
  const either = (): number => {
    let value = together();
    // Alternative licenses: a user may choose the more permissive route.
    while (take('OR')) value = Math.max(value, together());
    return value;
  };
  try {
    const factor = either();
    return pos === tokens.length ? factor : 1;
  } catch {
    return 1;
  }
}
