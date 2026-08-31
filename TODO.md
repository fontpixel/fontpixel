# TODO

## Per-page translations for the docs sections (`site/src/content/docs/`)

Deferred on 2026-08-31. The docs content collection (bdf-spec, bdfparser-js,
bdfparser-py, font-template) is currently English-only: `DOC_LANGS = ['en']` in
`site/src/lib/docs.ts` is a site-wide switch, and translated files are not yet
recognized. The intended convention — a translation lives next to the original
as `<name>.<lang>.mdx` (e.g. `examples.zh.mdx` beside `examples.mdx`;
`content.config.ts`'s `generateId` already preserves dots for this) — needs the
following plumbing before it works:

1. **Id resolution** (`site/src/lib/docs.ts`): split entry ids like
   `bdf-spec/examples.zh` into base slug `examples` + language `zh`. Translated
   entries must not appear as standalone pages in the English sidebar.
2. **Per-page routes**: generate `/zh/bdf-spec/examples/` only when
   `examples.zh.mdx` exists, rendering the translated entry. That page's
   `availableLangs` becomes `['en', 'zh']` — the language menu and hreflang
   alternates then appear automatically (that pipeline in `Base.astro` is
   already in place).
3. **Sidebar fallback**: on a translated page, sibling links for untranslated
   pages point back to `/en/…`.

**Traditional Chinese does not come for free.** The site's zh→zh-Hant
conversion (OpenCC + FIXUPS in `site/src/i18n/hant.ts`) only runs over TS
string values, not MDX bodies. To derive `/zh-Hant/` from a `.zh.mdx`, add a
remark plugin that converts text nodes in the MDX AST while skipping code
fences, frontmatter, and JSX attributes. Until then, a `.zh.mdx` yields
Simplified only; Traditional would need a hand-written `.zh-Hant.mdx`.

When the plumbing lands, the translation work itself must be delegated to
Opus/Sonnet subagents per the project's translation policy.
