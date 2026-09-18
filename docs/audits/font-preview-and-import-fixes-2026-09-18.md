# Preview size and import corrections, 2026-09-18

## Default preview size

The automatic default now prefers native sizes from 8px through 16px inclusive,
then selects the variant with the most glyphs within that range. If none is in
range, select the most complete variant from all sizes. Existing deterministic
variant order resolves ties. An explicit `default_variant` remains authoritative.

The rule is shared by fresh builds and cached metadata refreshes. Language
counterparts for the default preview stay within the eligible size range.
Sample language/text, card SVG, detail SVG, title SVG and OG image are refreshed
together. Coverage and family glyph totals still describe the whole family.

Dylex Terminal changes from `10x20` (5,263 glyphs) to `7x13` (3,298 glyphs),
because the latter has the most glyphs among the 10px and 13px candidates.

## Frogatto Numbers

Source: [Jetrel's Frogatto font sheets on OpenGameArt](https://opengameart.org/content/frogatto-friends-bitmap-fonts),
archive `https://opengameart.org/sites/default/files/frogatto-fonts.zip`.
The downloaded archive matches the originally imported PNGs:

| Sheet | SHA-256 |
| --- | --- |
| `number_font.png` | `3e4d4902221ac63e1e0ac4789d56ecc8b4305dbd62c13fb22fcc4c7a2ac28887` |
| `number-font-scrolling.png` | `515006ae1edfc1727cab398889f0914781fc8b5f9a0daca4ce6840ea8652b361` |

The old foreground palette included the dark inset/background colours inside
digits. Flattening those colours into monochrome filled the counters of 0 and 8.
Remove RGB `(152, 0, 97)` and `(153, 0, 48)` from the number-sheet foreground and
`(152, 103, 26)` from the scrolling foreground. Retain all other mapped pixels,
cell coordinates, advances, baselines, character mappings and four variants.
This is a reviewed monochrome extraction from coloured sprites, not a change
to the source sheets. The corrected palettes live in `ingest/manifest.toml` so
future imports reproduce the fix.

## Not Jam Chunky Sans 11

The [author's page](https://not-jam.itch.io/not-jam-chunky-sans-8) describes the
11px face as the same letter design with additional extended Latin support.
The original imported TTF has SHA-256
`468ed12633f2f88662947d5a277ff356da3fce02ff5e7ad616bc3123cc00f5ff`.

FreeType returns unhinted advances in 26.6 fixed-point units. The converter used
`advance.x >> 6`, truncating fractional values: A's 835 font units at 11px/1024
units per em are about 8.97px, which became an 8px advance despite its 8px ink.
Round to the nearest integer instead, giving a 9px advance and restoring its
1px right bearing. This also preserves zero advances and rounds values near
the lower integer down; it is not a blanket addition of letter spacing.

Regenerated the 11px BDF from the original TTF. All 300 encoded glyph bitmaps
are unchanged, all 300 advances gain their intended rounding pixel, and the
three unencoded glyphs are retained. The 6px and 8px BDFs are unchanged. The
shared rasterizer now uses correct advance rounding for future conversions.

## Poxiao Pixel CN and Hax

The [upstream 1.0.0 release](https://forge.poxiao-labs.work/Fonts/fzg/releases/tag/1.0.0)
really includes both `FZG_CN.ttf` and `FZG_HAX.ttf`. SHA-256:

| File | SHA-256 |
| --- | --- |
| `FZG_CN.ttf` | `6cb1358031977408a1ac50f4f3dda29e54d3fb4bd08931daa54366b14f55e8d9` |
| `FZG_HAX.ttf` | `b42ca82c65d621a08ef2628745fea32213a742ab177289720bc90e4adf4e9c7e` |

Their `cmap`, `glyf`, `hmtx`, `loca` and `post` tables are byte-identical.
The meaningful difference is in `GSUB`: Hax adds 80 programming-symbol
ligature rules, including `!=`, `=>` and `===`. The upstream
[feature selection](https://forge.poxiao-labs.work/Fonts/fzg/src/commit/1418a8e6126acaad2a0c23869f2a13331079d6d2/fzg/metadata.py)
adds `open-relay/features/ligatures.fea` only to the Hax build.

Both imported BDFs contain the same 50,763 encoded characters. Comparing each
character's advance, bounding box, offsets and bitmap finds zero differences.
The per-character conversion does not retain OpenType substitution rules,
including these ligatures and language-specific substitutions. The bitmap
previews and regenerated downloads therefore cannot demonstrate Hax's feature.
The previous description claiming different Latin glyphs was incorrect and
has been replaced with the verified distinction and a pointer to the original
upstream files. Only the regular (CN) build is now included in this catalogue;
the duplicate Hax bitmap conversion and its generated downloads were removed.
