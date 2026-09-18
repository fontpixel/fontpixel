# Complete Google Fonts imports — 2026-09-17

All eight requested families were absent from the admitted collection. Doto and Bitcount had older pending entries; this review supersedes those decisions for the specific Google Fonts releases below.

The inputs are complete TTFs from [google/fonts at `92345ac0dbb28d27dbd32f3a782e84c55eaac214`](https://github.com/google/fonts/tree/92345ac0dbb28d27dbd32f3a782e84c55eaac214). No CSS-sliced WOFF2 files were used. Each family retains its official OFL.txt. Source SHA-256 hashes, variation coordinates, coverage fingerprints, and per-file counts are recorded in [the machine-readable audit](google-fonts-import-audit-2026-09-17.json).

| Family | BDF variants | Grid ppem | Unicode characters per variant | Unencoded glyphs per variant |
| --- | ---: | ---: | ---: | ---: |
| Silkscreen | Regular, Bold | 8 | 226 | 2 |
| Micro 5 | Regular | 11 | 331 | 29 |
| Bytesized | Regular | 8 | 347 | 1 |
| Pixelify Sans | Regular, Medium, SemiBold, Bold | 11 | 574 | 6 |
| Jacquarda Bastarda 9 | Regular | 13 | 331 | 19 |
| Bitcount Single | Regular dot grid | 10 | 396 | 1,358 |
| Bitcount | Regular dot grid | 10 | 396 | 648 |
| Doto | Restored dot grid | 10 | 319 | 1 |

“Unicode characters” counts every cmap entry, including aliases and Silkscreen's blank U+000D. Counts are consequently not always equal to the source font's number of distinct glyphs. Bytesized has 20 cmap aliases, and Pixelify Sans has four. BDF files retain unencoded alternates, ligatures, components, and `.notdef` with their original names and `ENCODING -1`; no invented Unicode or private-use assignments are introduced.

## Conversion decisions

- **Micro 5, Bytesized, Jacquarda Bastarda 9:** detected exact outline grids of 150, 2, and 80 font units respectively, corresponding to 11, 8, and 13 ppem. Micro 5's name refers to its five-pixel capitals, not the em size.
- **Silkscreen:** the intended grid is 125 units at 1,000 upem, or 8 ppem. Small outline corrections such as y=495 beside y=500 prevent a strict gcd detector from finding it. Both weights were reviewed and converted without hinting at the intended size.
- **Pixelify Sans:** the outlines include optical adjustments and do not sit on one exact integer grid. The four official named weight instances, wght 400/500/600/700, are manually rasterized at 11 ppem and preserve their distinct bitmaps. This is a quantized bitmap conversion, not a mathematically lossless reversal of vector outlines. Latin, extended Latin, and Cyrillic remain complete in every weight.
- **Bitcount / Bitcount Single:** use wght=400, ELXP=0, ELSH=0, slnt=0, CRSV=0. The 100-unit dot spacing at 1,000 upem becomes one pixel per dot at 10 ppem. Dot shape, continuous weight interpolation, slant, and colour effects are not retained in this fixed monochrome representation.
- **Doto:** use wght=900, ROND=100 at 10 ppem. The round-dot and square-dot endpoints produce identical restored text bitmaps at this size, confirming that dot positions are retained. The continuous weight/roundness axes collapse to a single fixed dot grid.
- A few **unencoded Bitcount component glyphs** centre their dots at integer grid intersections, while their uses in text are translated to pixel centres. Explicit +0.5px x/y offsets preserve `circle`, `raster`, `el_circle`, and `el_raster` as visible bitmaps. Only the latter two exist in Bitcount Single. Text glyphs are not shifted. The standalone circle is one pixel; the raster is a 7×7 pattern containing 25 pixels.

Every source cmap mapping was compared with the emitted BDF, including supplementary-plane mappings where present. Every source glyph name is represented either by an encoded glyph or an unencoded BDF glyph. A separate geometry check found **zero visible source glyphs becoming blank** after the recorded conversions, including the unencoded glyphs.

The original source BDFs and their unencoded glyphs are preserved in BDF, PCF, and ZIP downloads. The site's Unicode grid and generated TTF/WOFF2 exports operate on encoded characters; they do not reproduce OpenType GSUB/GPOS shaping, contextual selection, or variation axes. Unencoded alternates remain available by name in the complete BDF files.

## Validation

The relevant pipeline suite passed 61 tests; site unit tests passed 66 tests. The production build and 63 Playwright tests passed, covering all eight new font previews and complete BDF downloads, Pixelify Sans Cyrillic across all four weights, existing import checks, navigation, and responsive layouts. All six generated language homepages use the `FontPixel` title prefix and a colon. The final catalogue has 210 families; the removed t-mat font is absent from generated pages, sitemaps, catalogue data, and downloads.

## Reproduction

The import manifest points to `direct-downloads-2026-09-17/google-fonts-<upstream-directory>` in the sibling source collection. Each directory contains the pinned official TTFs, OFL.txt, METADATA.pb, and source.json with file hashes.

```bash
.venv/bin/python -m opf.ingest.run --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts --dest fonts --only micro-5
```

Use the family slugs `silkscreen`, `micro-5`, `bytesized`, `pixelify-sans`, `jacquarda-bastarda-9`, `bitcount-single`, `bitcount`, or `doto`. `all_glyphs = true` retains controls and unencoded glyphs; `instances` pins variable-font coordinates; `glyph_offsets` records the few component-grid corrections. Repeating an import must leave all BDF bytes unchanged.

Audit fingerprints are SHA-256 over UTF-8 JSON with sorted keys, no whitespace, and non-ASCII characters retained. `cmap_sha256` fingerprints the Unicode-to-original-glyph-name mapping; `unencoded_names_sha256` fingerprints the sorted names of unencoded glyphs. Cmap aliases receive `.U<codepoint>` suffixes in BDF names so STARTCHAR names remain unique; remove that generated suffix when verifying the original cmap fingerprint.

Subsequent consolidation: Bitcount Single and Bitcount Prop Single now live in the `bitcount` family. Reimport with `--only bitcount`; the corresponding BDF bytes are unchanged. See [the six-variant consolidation audit](bitcount-family-audit-2026-09-17.md).
