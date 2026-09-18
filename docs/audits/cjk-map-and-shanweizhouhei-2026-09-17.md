# CJK coverage map and ShanWeiZhouHei 16

## Font import

- Family: `shanweizhouhei-16`, 扇尾胄黑16 / ShanWeiZhouHei 16.
- Upstream: https://github.com/yzdnn/ShanWeiZhouHei-16
- Revision: `f0373bc2183778615d6ae4ff56fd2b9c5511ce25`.
- Source: `Fonts/ShanWeiZhouHei-16.ttf`.
- SHA-256: `06d2507c4778e5c98725e92ad3387302f5ed8dd0b285ff73a9aab4cf392184e4`.
- Converted at the documented 16px size, without hinting; all glyphs retained.
- All 11,794 Unicode mappings retained. The BDF also retains 391 unencoded
  glyphs. Three cmap aliases account for the difference between 12,182 source
  glyphs and 12,185 BDF entries.
- Upstream OFL and copyright notices are included. The converted font's
  internal family name is `FontPixel SWZH 16`, respecting the names reserved
  in the upstream README. The catalogue retains the upstream project name.
- Same forms and vibes as FashionBitmap16: `gothic`, `decorative`, `sans`;
  `game-ui`. Both derive from KH Dot Kabutochou 16.
- The repeatable import configuration is in `ingest/manifest.toml`.

## Diagram definitions

`CjkCoverage.astro` adapts the supplied
`cjk_character_sets_euler_v3_measured.svg`. The drawing is schematic and its
areas are not proportional to counts. Each figure is computed for the selected
variant, including intersections, differences and the deduplicated union.

The original approximate figures are replaced by the repository's reference
tables and Unicode 17 assigned code points:

| Set | Total | Definition |
| --- | ---: | --- |
| Unified Han | 101,996 | Unified blocks plus the 12 unified ideographs in the compatibility block |
| Taiwan | 11,151 | Common 4,808 plus less-common 6,343 |
| China | 8,105 | Three levels: 3,500, 3,000, 1,605 |
| Japan | 2,136 | Jōyō kanji |
| Korea | 4,620 | KS X 1001 unified Han; 268 compatibility characters counted separately |
| Four-table union | 14,818 | Exact code-point union of the above four national lists |
| Kana | 579 | Hiragana 93, Katakana 96, extensions 327, halfwidth 63 |
| Hangul syllables | 11,172 | Precomposed syllables; KS X 1001 subset 2,350 |
| Jamo | 451 | Jamo, compatibility Jamo, extensions A and B |
| Bopomofo | 75 | Assigned base and extended block characters |
| Selected CJK combined | 26,644 | Four-table Han union plus Kana, Hangul syllables and Bopomofo |

There is no Unicode normalization: a compatibility glyph does not imply a
glyph at its unified counterpart, and language-specific glyph shapes cannot
be established from code-point coverage. The details disclosure documents this
and includes all subset, intersection and unique-character counts from the
original diagram. This map's complete Unicode kana blocks intentionally have
larger totals than the existing kana-letter-only coverage rows (86 and 90).

The September 18 refinement promotes the selected CJK combined count and its
percentage to the primary summary. The full unified-Han count is a smaller
context row without a percentage. The four-table union remains in the details,
as do Jamo and compatibility Han, which are not included in the selected total.
The summary deliberately says “selected” because its kana include historical
and extended characters. Geographic labels identify Mainland China explicitly
in every locale, and the details disclosure has a connected border.

Intersection and difference labels identify the writing-system sets (Traditional
Han, Simplified Han, Japanese Kanji and Korean Han) rather than countries or
regions. Geographic labels remain on the map and in the definitions to identify
the sources of the reference tables. Chinese retains the compact 繁／简／日／韩 notation.

The English overlap label is “Simp Trad Shared”. All locales explain that it
counts shared Unicode code points, which may still have different regional
glyphs, for example through [OpenType locl localized substitutions](https://learn.microsoft.com/en-us/typography/opentype/spec/features_ko#locl).
The map measures code-point coverage and does not test glyph-shape equivalence
or claim that each catalogued font implements this OpenType feature.

## Build and presentation

`coverage/cjk.py` enriches both freshly built and cached details using canonical
Unicode BDF downloads. A hash of the set definitions and per-variant source
hashes invalidates these small summaries without regenerating font outlines.
The detail contract is version 5; the glyph pipeline version is unchanged.

The map follows both variant selectors and is included in coverage-panel
deduplication. Desktop uses the adapted SVG; narrow containers use equivalent
readable summaries. Meters, exact fractions, SVG descriptions and expandable
HTML tables cover visual and assistive reading. Copy is available in all six
site languages, with Traditional Chinese derived using the existing converter.
