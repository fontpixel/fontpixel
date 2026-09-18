# DotGothic16 and manually lowered families, 2026-09-18

## DotGothic16 correction

Reimported the complete [Google Fonts TTF at pinned commit
9a6cc6b8ce992aff77b69c857c46af0b42cdff76](https://github.com/google/fonts/tree/9a6cc6b8ce992aff77b69c857c46af0b42cdff76/ofl/dotgothic16).
The TTF SHA-256 is
`3ad9af88726d42b40f7f365f0dcac785af73cf20ea6f1d5b44e57cc21150b8f1`.

The previous hinted import thickened and joined some strokes: notably the top
vertical of を and the lower-right diagonal of は. Disabling hinting alone is
insufficient because these outlines sit off the sampling grid. A half-pixel
translation fixes those kana but still thickens some Cyrillic letters and box
drawing. The final import disables hinting and translates both axes by 45/64px
(0.703125px), expressed explicitly in the manifest's `pixel_offset` setting.
Other families retain their existing rasterization settings.

Checked every encoded outline independently: decompose components, scale to
16px, translate, round the path vertices to the grid, then scan-convert using
nonzero winding. All 8,231 encoded bitmaps match this reconstruction. The 1,392
unencoded glyphs are also retained. Two narrow halfwidth quotation alternates,
`quotedblright.half` and `quoteright.half`, retain three extra pixels each through
FreeType's thin-stroke dropout handling; no manual bitmap edits were applied.

The complete source contains 9,362 glyphs; cmap aliases account for the larger
number of BDF entries. Compared with the previous import, 4,717 encoded bitmaps
change, one control mapping is restored, and no previously visible encoded
character becomes blank. All source glyph names and cmap entries are retained.
Per-character bitmap conversion still does not preserve OpenType shaping rules.

Rebuilt browser data, previews and BDF/PCF/TTF/WOFF2 downloads. DotGothic16's
−0.5 aesthetic adjustment is removed; the separate Google Fonts preference is
documented in the [current rating policy](../specs/catalogue-rating.md).
Source, coverage and geometry fingerprints are recorded in
[the machine-readable audit](dotgothic16-import-audit-2026-09-18.json).

## Remaining aesthetic deductions

All nine families below retain their existing −0.5 adjustments: no import
thickening or joining was found. These are the owner's aesthetic preferences.

| Family | Checked source | Result |
| --- | --- | --- |
| Misc Fixed | 25 native BDF files from X.Org font-misc-misc 1.1.3 | All byte-identical |
| DOSGothic | 1 upstream BDF | Byte-identical |
| DOSSaemmul | 1 upstream BDF | Byte-identical |
| Baekmuk Batang | 14 upstream BDFs | All byte-identical |
| Baekmuk Dotum | 7 upstream BDFs | All byte-identical |
| Baekmuk Gulim | 14 upstream BDFs | All byte-identical |
| Baekmuk Hline | 7 upstream BDFs | All byte-identical |
| 1307 | Original PNG sprite sheet | All 95 characters and 14 UI tiles match |
| jiskan | Five original JF-Dot TTFs, unhinted at 16px/24px | All 52,684 encoded glyphs match independent grid reconstruction |

The 69 native BDF files and the PNG import never pass through a TTF hinter.
jiskan is reproduced identically with hinting disabled, including advances;
its pixel geometry also passes the independent outline check above without an
offset. No source font was changed for this audit.

Misc Fixed was checked against the official
[X.Org release archive](https://xorg.freedesktop.org/releases/individual/font/font-misc-misc-1.1.3.tar.xz).
All filenames, counts, hashes and jiskan grid-check results are recorded in
[the penalty audit](penalized-font-import-audit-2026-09-18.json).
