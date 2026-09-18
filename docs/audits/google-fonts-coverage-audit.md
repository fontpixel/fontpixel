# Google Fonts coverage audit — 2026-09-17

This is the initial coverage snapshot. DotGothic16 was subsequently reimported
with corrected pixel alignment and all cmap entries/unencoded glyphs; see the
[September 18 correction](dotgothic16-import-audit-2026-09-18.md).

Compared the Unicode cmap of the complete official TTFs in [google/fonts at `92345ac0dbb2`](https://github.com/google/fonts/tree/92345ac0dbb28d27dbd32f3a782e84c55eaac214) against the union of the imported BDF code points for each matching family. Counts below exclude upstream control code points below U+0020, consistent with the TTF rasterizer. Matching used family names and upstream authors/repositories, not only directory names.

| Family | Before | Official TTF | Missing from local before | Result |
| --- | ---: | ---: | ---: | --- |
| Press Start 2P | 218 | 654 | 436 | Replaced the Latin-only CSS slice with the complete v3.000 TTF; now 654. |
| DotGothic16 | 8,230 | 8,230 | 0 | Exact code-point match, including Japanese and Cyrillic. |
| Tiny5 | 1,654 | 1,154 | 23 | Native upstream BDF v2.003 versus older Google Fonts TTF v1.002; see below. |
| Yarndings 12 | 93 | 93 | 0 | Exact code-point match (a pictographic font using Latin code-point slots). |
| Yarndings 20 | 93 | 93 | 0 | Exact code-point match (a pictographic font using Latin code-point slots). |

Only Press Start 2P was imported directly from the `Google-Fonts` CSS export directory. Its old manifest explicitly selected `font-05.woff2`, leaving out four other slices. The other directory in that snapshot, VT323, is excluded from this collection because its outlines do not meet the native pixel-grid criterion; it is not a partially imported font.

DotGothic16, Tiny5, and both Yarndings families came from their authors' repositories. No second Latin-only import was found among the admitted Google Fonts families. The site's Lemon by king benis/phallus is unrelated to Google Fonts' Lemon by Eduardo Tunni and is excluded from this comparison.

## Press Start 2P fix

- Source: [complete PressStart2P-Regular.ttf](https://github.com/google/fonts/blob/92345ac0dbb28d27dbd32f3a782e84c55eaac214/ofl/pressstart2p/PressStart2P-Regular.ttf), version 3.000.
- SHA-256: `034c77f1f05ec89421e4a63f0e3a4ca1ecf852cc6d2bf611f126f275728e017d`.
- Licence: upstream OFL.txt, retained with the font.
- Rasterized at its native 8px size, without hinting. Every cmap entry at or above U+0020 survived the conversion; no rasterization warnings.
- All 218 previously imported glyphs retain exactly the same pixels, bitmap bounds, offsets, and advance widths.
- Added 436 encoded characters. The complete result includes 74 code points in Greek and Coptic (U+0370–03FF) and 184 in the Cyrillic ranges U+0400–052F, alongside extended Latin, combining marks, and punctuation.
- The import manifest now selects the complete TTF. Regression tests assert Greek, Cyrillic, and extended Latin coverage in the committed BDF.

## Tiny5 version differences

The native BDFs are version 2.003 (2026), while Google Fonts still supplies version 1.002 (2024). Both sources include Greek and Cyrillic. The native BDF union contains 523 code points absent from the older Google Fonts TTF, while that TTF contains the following 23 code points absent from the native BDFs:

U+02BD, U+0310, U+0334, U+0358, U+1D5B, U+2015, U+201B, U+201F, U+2023, U+2024, U+2025, U+2031, U+2034, U+2037, U+2249, U+25BA, U+25BB, U+25C4, U+25C5, U+A726, U+A727, U+A7A8, U+A7A9.

This is a version/source difference, not a discarded non-Latin CSS slice. The newer native bitmap source has been retained; the two generations were not mixed into a synthetic font.

## Reproduction

The manifest records the complete Press Start 2P input under `direct-downloads-2026-09-17/google-fonts-pressstart2p` in the source collection. Reimport with:

```bash
.venv/bin/python -m opf.ingest.run --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts --dest fonts --only press-start-2p
```
