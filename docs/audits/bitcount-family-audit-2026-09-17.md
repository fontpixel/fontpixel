# Bitcount family consolidation

The collection now has one **Bitcount** family with six 10px variants. **Bitcount Single is the default preview in every site language**, including the catalogue, sample editor, and coverage selector.

| Variant | Encoded characters | Unencoded glyphs |
| --- | ---: | ---: |
| Bitcount Single (default) | 396 | 1,358 |
| Bitcount | 396 | 648 |
| Bitcount Grid Double | 396 | 313 |
| Bitcount Prop Single | 396 | 1,595 |
| Bitcount Grid Single | 396 | 791 |
| Bitcount Prop Double | 396 | 731 |

All variants use complete official TTFs from [google/fonts at `92345ac0dbb28d27dbd32f3a782e84c55eaac214`](https://github.com/google/fonts/tree/92345ac0dbb28d27dbd32f3a782e84c55eaac214/ofl), pinned to wght=400, ELXP=0, ELSH=0, slnt=0, CRSV=0. All source cmap entries and original glyph names are retained. A geometry check found no visible source glyph becoming blank, including unencoded alternates and components. The three previously imported BDFs were copied into the combined family without changing their bytes.

The original dot grids are restored at 10px. As in the earlier Bitcount imports, standalone unencoded `el_circle` and `el_raster` use a +0.5px x/y correction; the legacy Bitcount also applies it to `circle` and `raster`. Text glyphs are not shifted. The Prop variants retain proportional advances. BDF/PCF/ZIP retain unencoded glyphs; the site's Unicode grid and derived TTF/WOFF2 expose encoded characters, without OpenType shaping or variable axes.

All variants have the same copyright notice and OFL terms. The legacy Bitcount licence uses a different licence-website URL; its complete official OFL.txt is bundled with the family. Source hashes, complete cmap/name and pixel fingerprints, axis settings, and component offsets are recorded in [the JSON audit](bitcount-family-audit-2026-09-17.json).

The former `bitcount-single` and `bitcount-prop-single` catalogue entries and their generated assets/downloads are removed. Their font-page URLs redirect to the combined `bitcount` page in all six languages. The former names remain searchable, returning one family. Historical audits use `current_family = bitcount` to locate the preserved BDFs.

Validation passed: 70 relevant pipeline tests, 15 frontend unit tests, and the browser suite covering all six Bitcount variant downloads/previews, Single as the default in every language, former-page redirects, and a single catalogue result. The production build passed. At consolidation time the collection had **212 families** after removing the two duplicate family entries.

```bash
.venv/bin/python -m opf.ingest.run --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts --dest fonts --only bitcount
```

The manifest selects each complete source file with its own named instance. Reimporting the combined family was verified to leave the BDFs unchanged.

## Prop Single import details

The earlier standalone Prop Single import is now part of this family. Its complete official source SHA-256 is `e6f39bb11077484a1becaf94b712331b5c2d169a27b4a4591f6ab70c901a8405`.

The Regular instance uses wght=400, ELXP=0, ELSH=0, slnt=0, CRSV=0, at **10px**. Every encoded glyph is assembled from the same `px` element on an exact 100-unit grid at 1000 upem. Each original dot becomes one pixel. Every encoded bitmap was independently compared with the recursively resolved source component positions; there are zero pixel mismatches.

The BDF retains **396 encoded characters and 1,595 unencoded glyphs**, covering all 1,991 source glyphs and all original cmap entries. This includes the complete Latin and extended-Latin repertoire, combining marks, symbols, alternates, and components. Every source-visible glyph remains visible, and every advance width matches its original value divided by 100. Two standalone unencoded components, `el_circle` and `el_raster`, require the same explicit +0.5px x/y offset used for Bitcount Single; they retain one and 25 lit pixels respectively. Text glyphs are not shifted.

This is a proportional face, not a duplicate of the existing monospaced Bitcount Single:

| Character | Bitcount Single advance | Bitcount Prop Single advance |
| --- | ---: | ---: |
| space | 6px | 3px |
| I | 6px | 3px |
| W | 6px | 11px |
| i | 6px | 2px |
| m | 6px | 10px |

The [JSON audit](google-fonts-bitcount-prop-single-audit-2026-09-17.json) records source hashes, axis settings, cmap/name fingerprints, and bitmap geometry fingerprints. No new private-use assignments are invented. Unencoded glyphs keep their source names and `ENCODING -1` in complete BDF/PCF/ZIP downloads. Generated TTF/WOFF2 and the site's Unicode glyph grid cover encoded characters; OpenType shaping rules and variable axes are not retained in those bitmap-derived exports.
