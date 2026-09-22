# CJK coverage map and ShanWeiZhouHei 16

## Font import

- Family: `shanweizhouhei-16`, 扇尾胄黑16 / ShanWeiZhouHei 16.
- Catalogue author: `yzdnn`.
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
| Japan | 2,965 | JIS X 0208 Level 1 kanji |
| Korea | 4,620 | KS X 1001 unified Han; 268 compatibility characters counted separately |
| Four-table union | 14,901 | Exact code-point union of the above four national lists |
| Kana | 579 | Hiragana 86, Katakana 90, additional characters 13, extensions 327, halfwidth 63 |
| Hangul syllables | 11,172 | Precomposed syllables; KS X 1001 subset 2,350 |
| Jamo | 451 | Jamo, compatibility Jamo, extensions A and B |
| Bopomofo | 75 | Assigned base and extended block characters |
| Selected CJK combined | 26,727 | Four-table Han union plus Kana, Hangul syllables and Bopomofo |

There is no Unicode normalization: a compatibility glyph does not imply a
glyph at its unified counterpart, and language-specific glyph shapes cannot
be established from code-point coverage. The details disclosure documents this
and lists 16 intersection, union and unique-character rows, in that order. Repeated
reference-set and script tables have been removed. Jōyō remains in the normal
Japanese coverage table; the map now uses the same JIS Level 1 set as the
catalogue's Japanese coverage criteria.

The disclosure includes Traditional ∪ Simplified (14,357), Traditional ∪
Simplified ∪ Japanese (14,694), and Traditional ∪ Simplified ∪ Korean (14,617),
followed by the four-table union (14,901).
The corresponding three-way intersections contain 1,771 and 2,733 characters;
the four-way intersection contains 1,698. The former (Korean ∩ Simplified) −
Traditional row has been removed. Each union counts shared code points once.
Traditional-only (4,638) and Simplified-only (3,028) precede Japanese-only and
Korean-only. Each exclusive set excludes all three other reference sets.

The September 18 refinement promotes the selected CJK combined count and its
percentage to the primary summary. The full unified-Han count is a smaller
context row without a percentage. Jamo and compatibility Han are not included
in the selected total.
The summary deliberately says “selected” because its kana include historical
and extended characters. Geographic labels identify Mainland China explicitly
in every locale, and the details disclosure has a connected border.

Every main-map total appears as a numeric row in the subsequent coverage tables.
The 579-kana total contains Hiragana 86, Katakana 90, additional characters 13,
extensions 327 and halfwidth kana 63. The 451-Jamo total contains compatibility
Jamo 94, the base block 256 and extensions A/B 101. The Taiwan total precedes
its common and less-common tables. KS X 1001 Han contains separate unified
4,620 and compatibility 268 rows. Numeric rows and indentation express these
relationships without explanatory row notes. Missing-character dialogs are
available whenever at most 500 characters are missing, including aggregate rows.
Unified Han and the selected CJK total have a summary table after the map.
The overview and map both include the 12 unified ideographs in compatibility
blocks in unified Han, excluding them from the compatibility total.

Totals precede their indented, muted subsets in the normal coverage tables:
GB/T 2312 levels, the three standard-Chinese levels, the two modern-common
Chinese lists, Big5 common/less-common, Jōyō/education kanji, and modern Hangul/
KS X 1001 syllables. Halfwidth kana is grouped under the kana total; JIS X 0201
remains a separate overlapping reference. The cumulative GB 18030 levels
are nested as 3 → 2 → 1. This is a display hierarchy; filter and index order stay
the same. Distinct standards are not nested merely because their sets overlap.

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
