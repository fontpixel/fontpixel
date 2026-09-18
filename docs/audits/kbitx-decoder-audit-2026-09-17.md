# kbitx decoding correction and MuzaiPixel deduplication

The two MuzaiPixel variants represented the same source design. `MuzaiPixel.bdf` came from native `MuzaiPixel.kbitx`; `MuzaiPixel-12px.bdf` was a rasterization of `MZPXorig.ttf`. Both original files identify version **2.0.20241013**, and contain the same 15,932 characters.

The apparent differences were caused by the collection's kbitx decoder. The [official WIBInputStream](https://github.com/kreativekorp/bitsnpicas/blob/master/main/java/BitsNPicas/src/com/kreative/bitsnpicas/WIBInputStream.java) uses the low five opcode bits as the run length and bit `0x20` as a multiplier of 32. The old decoder treated all six low bits as an ordinary length. For example, U+2588 has the actual payload `DAhj`: a 12×8 bitmap followed by opcode `0x63`. That opcode means 96 solid pixels; the old decoder produced 35. The [official kbitx importer](https://github.com/kreativekorp/bitsnpicas/blob/master/main/java/BitsNPicas/src/com/kreative/bitsnpicas/importer/KbitxBitmapFontImporter.java) also reads dimensions as unsigned LEB128 integers, which the old decoder had treated as single bytes.

Both decoding rules are now corrected. Regression tests cover transparent, solid, repeated-grayscale, and literal-grayscale long runs; the short-run boundary; multi-byte dimensions; and MuzaiPixel's actual full-block payload. Every character in the official Galmuri 9 BDF is compared with its native kbitx conversion, replacing the previous partial sample comparison. All **15,932 MuzaiPixel characters** are compared with the corresponding official TTF, including absolute pixel positions and advance widths; all match.

## MuzaiPixel result

- Retain only the native `MuzaiPixel.bdf` at 12px, with the existing 15,932-character coverage.
- Correct the eight affected characters: U+2586, U+2587, U+2588, U+2589, U+258A, U+25CF, U+30CB, U+4E8C (`▆ ▇ █ ▉ ▊ ● ニ 二`).
- Remove the duplicate TTF-derived `MuzaiPixel-12px.bdf` and its generated variant assets/downloads.
- Correct the provenance text to describe the native source and its actual version. Keep the complete upstream `LICENSE.md` as the declared licence source.
- Keep the manifest on its existing kbitx source, so imports do not recreate the duplicate.

## Other admitted kbitx fonts

All 15 kbitx files selected by the active manifest were audited. Before regeneration, their committed BDF glyphs were checked against the previous decoder to ensure that no separate manual glyph edits would be overwritten. After correcting the decoder, every character set remained unchanged. Thirteen files across seven families needed pixel corrections; two files were unchanged.

| Family | Files checked | Files with pixel corrections | Corrected glyphs across variants |
| --- | ---: | ---: | ---: |
| Z Labs Pixel 12px | 3 | 3 | 142 |
| Z Labs DiamondPix 16px | 1 | 1 | 32 |
| Z Labs RoundPix | 3 | 3 | 141 |
| MuzaiPixel | 1 | 1 | 8 |
| Chenhao RP Font | 3 | 1 | 3 |
| CLFN | 3 | 3 | 196 |
| Liora Chip 10x12 | 1 | 1 | 17 |
| **Total** | **15** | **13** | **539** |

The unchanged files are `Chenhao_RP_Font_Enchant.kbitx` and `Chenhao_RP_Font_Supplement.kbitx`. All seven families were reimported and their site data, previews, BDF, PCF, and TTF/WOFF2 downloads regenerated. Deduplication does not change the number of font families.

The [machine-readable audit](kbitx-decoder-audit-2026-09-17.json) records each source path/hash, character count, affected code points, and old/new warning counts. The corrected decoder emits no warnings for these sources. The remaining empty t-mat source folder's unrelated build warning predates this work.

Final validation: 55 relevant pipeline tests and 19 browser tests passed, including the new complete Bitcount Prop Single import. All seven kbitx families reimport without changes. The MuzaiPixel browser test checks its single native variant, the corrected 96-pixel full block in the downloaded BDF, and HTTP 404 responses for the removed duplicate BDF and glyph pack. The production site build also passed.

Reproduce the retained MuzaiPixel import with:

```bash
.venv/bin/python -m opf.ingest.run --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts --dest fonts --only muzai-pixel
```
