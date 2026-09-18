# Jacquard, Jersey, and Handjet — complete Google Fonts import

Reviewed on 2026-09-17. None of the seven requested Google Fonts faces was previously admitted. They are now grouped into three families: **Jacquard** (12 and 24), **Jersey** (10, 15, 20, 25), and **Handjet**. The previously imported Jacquarda Bastarda 9 is a separate design and remains separate.

All inputs are complete official TTFs from [google/fonts at `92345ac0dbb28d27dbd32f3a782e84c55eaac214`](https://github.com/google/fonts/tree/92345ac0dbb28d27dbd32f3a782e84c55eaac214). No CSS subsets were used. Every cmap entry and every unencoded glyph is retained in BDF. Source hashes, script counts, complete cmap/name fingerprints, and independently verified pixel-geometry fingerprints are in [the JSON audit](google-fonts-jacquard-jersey-handjet-audit-2026-09-17.json).

| Site family | Official face | BDF size | Unicode characters | Unencoded glyphs |
| --- | --- | ---: | ---: | ---: |
| Jacquard | Jacquard 12 | 21px | 331 | 26 |
| Jacquard | Jacquard 24 | 43px | 331 | 26 |
| Jersey | Jersey 10 | 19px | 332 | 31 |
| Jersey | Jersey 15 | 27px | 332 | 30 |
| Jersey | Jersey 20 | 34px | 332 | 30 |
| Jersey | Jersey 25 | 41px | 332 | 30 |
| Handjet | Regular square elements | 34px | 1,339 | 266 |

## Native-grid decisions

The original Jacquard/Jersey numbers are upstream design names referring to nominal capital heights, not the full em size used by BDF. The site describes the correspondence and keeps the original names as search aliases and in download filenames.

- **Jacquard 12/24:** all contours of every glyph are axis-aligned polygons on exact 60/30-font-unit grids. Their upem values are 1260/1290, giving native em sizes of 21/43 pixels. These are direct grid recoveries, including decorative overshoots. See the author's [Jacquard project](https://github.com/scfried/soft-type-jacquard).
- **Jersey 10/15/20/25:** the original grids are 75/50/38/30 font units. The capital `A` and `H` heights after conversion are exactly 10/15/20/25 pixels. These are four sizes of one family, as requested. See the author's [Jersey project](https://github.com/scfried/soft-type-jersey).
- **Jersey 10:** its 1400-unit em is not divisible by its 75-unit grid. Choosing the nearest integer ppem without compensating would stretch the bitmap. The explicit manifest `grid_units` override changes the in-memory em to 1425, then renders at nominal 19px. Every original 75-unit cell becomes one pixel, with every advance width preserved exactly. Original TTF bytes are unchanged. Hinting is disabled, and the importer rejects combining this override with hinting.
- **Jersey 25:** one small extra rectangle in `emdash`, at x=106..121 and y=-276..-271, is off the otherwise exact 30-unit grid. This 15×5-unit contour covers no native pixel centre and disappears at the intended size; the complete em-dash glyph and all other glyphs remain. It is recorded explicitly in the audit rather than treating a stray subpixel contour as evidence that the entire family is a vector-only design.
- **Handjet:** the official [axis documentation](https://github.com/rosettatype/handjet#variable-font) identifies ELSH=2 as the square element. The imported instance pins wght=400, ELGR=1, ELSH=2. In the actual Google Fonts file, all 1,605 glyphs are recursively assembled from the same 480×480-unit square. Every component translation is an exact multiple of 240 units, including half-cell positions; there are no rotated or scaled components. At 8160 upem, 34px therefore preserves every square as 2×2 pixels and every half-cell shift as one pixel. A 17px rendering would discard those half-cell positions. The other variable weights, element shapes, and grouping effects are not separately imported as bitmap styles.

## Complete coverage and independent geometry checks

Jacquard and Jersey retain their complete Latin/extended-Latin characters, combining marks, punctuation, mathematics, and symbols. Handjet retains all six scripts in the official Google Fonts file: Latin, Greek, Cyrillic, Armenian, Hebrew, and Arabic, as well as the font's existing private-use assignments. The current author-repository README also mentions Korean, but the pinned Google Fonts TTF contains no Korean script mappings; no Korean glyphs were discarded by the conversion.

All **3,768 source glyphs across seven files** were checked, including `.notdef`, alternate forms, and contextual glyphs:

1. Compare every Unicode-to-glyph-name mapping and all unencoded names with the original complete TTF.
2. For Jacquard and Jersey, independently fill the axis-aligned source polygons using nonzero winding at native pixel centres and compare the resulting absolute pixel positions with the BDF.
3. For Handjet, recursively resolve each `pixel` component and independently reconstruct its 2×2 square on the 240-unit grid, then compare with the BDF.
4. Compare every advance width with its original hmtx width divided by the verified grid interval.

The results are **zero missing characters, zero missing glyphs, zero pixel mismatches, and zero advance-width differences**. Font previews were also visually inspected. The only off-grid contour exception is the explicitly documented Jersey 25 rectangle above.

Unencoded glyphs keep their original names and `ENCODING -1`; no new Unicode or private-use assignments are invented. Complete BDF/PCF/ZIP downloads retain those glyphs. The site's Unicode grid and derived TTF/WOFF2 exports cover encoded characters. BDF does not encode OpenType GSUB/GPOS rules, so Handjet's contextual Arabic glyphs remain available by name without automatically recreating Arabic joining or mark positioning.

## Licences and reproduction

Each family retains the complete official OFL.txt. Both Jacquard sizes have byte-identical notices, as do all four Jersey sizes; one unchanged notice is bundled with each grouped family. Handjet retains its own official notice.

The import manifest selects complete TTFs under `direct-downloads-2026-09-17/google-fonts-<upstream-directory>` in the sibling source collection. Those directories retain METADATA.pb and source.json with pinned checksums. Reimport each family with:

```bash
.venv/bin/python -m opf.ingest.run --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts --dest fonts --only jacquard
```

Replace `jacquard` with `jersey` or `handjet` for the others. All three repeated imports were verified to make no changes. The new explicit-grid conversion and the complete import checks passed the relevant 40-test pipeline suite. The production site build and 17 browser tests passed, including all new variant previews/downloads, the six Handjet scripts, and searching each original Jacquard/Jersey name as one grouped family. The catalogue now contains **213 families**.
