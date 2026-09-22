# Catalogue rating

Current policy, 2026-09-18. Implementation: [rating.ts](../../site/src/lib/rating.ts).

Auto (自动) replaces Random as the default catalogue sort in all six languages.
Its fixed rating estimates practical character coverage at useful pixel sizes,
with a small preference for easier licensed reuse and explicit aesthetic adjustments.
Existing name, size and glyph-count sorts remain.
The owner's aesthetic adjustments are separate from the automatic calculation.

## Formula

`automaticScore = core × (90 + 8 × depth + language + terminal) × sizeFactor × licenseFactor`

`score = max(0, automaticScore + adjustment + googleFontsBonus)`

The automatic part is on a 0–100 scale; the final sort score may exceed 100.
Coverage remains the main component; license preferences can reduce the
automatic result by at most 4%.

All coverage inputs are the same 0–1 family-level ratios used by the coverage
filters: the maximum available across variants, not a union of complementary
incomplete fonts. A family is assessed as a collection; its best size and its
best coverage need not occur in the same variant. Detail pages remain the place
to check a particular variant's exact coverage.

### Main writing system

| Target | Coverage reference |
| --- | --- |
| Simplified Chinese | Better coverage of GB 2312 and 通用规范汉字表 |
| Traditional Chinese | Big5 common characters |
| Japanese | 70% JIS X 0208 level 1 kanji + 30% of the lower hiragana/katakana coverage; both kana sets must reach 95% |
| Korean | Better coverage of KS X 1001's 2,350 common syllables and all modern Hangul syllables |
| Latin | Basic Latin printable characters |
| Cyrillic, Greek, Arabic, Thai | The corresponding coverage-filter chart |

When CJK coverage indicates a target (at least 10%, as in script detection),
evaluate each eligible CJK profile and use its highest final score. Complete
ASCII cannot hide incomplete CJK coverage.
Shared Han does not impose several independent language obligations on a
Japanese or Chinese font. Complete kana with no kanji is still credited as
partial Japanese. Otherwise evaluate the alphabets, including Latin, so
incidental or incomplete support of another alphabet never lowers the score.
These are inferred coverage targets, not claims about the author's intent.
Selecting by the entire score, including the depth bonus below, also avoids a
score decrease when increasing coverage switches the strongest primary script
to one with a less-complete supplemental chart. Ties use the fixed profile order
(Simplified, Traditional, Japanese, Korean; otherwise Latin, Cyrillic, Greek,
Arabic, Thai).

For CJK, `core = sqrt(coverage)`; for other alphabets, `core = coverage`.
Thus 64% of a large CJK reference set receives 80% core credit. Korean fonts can
receive full core credit for the common KS set without drawing 11,172 syllables.
No score uses the full Unicode Han repertoire as a denominator.

### Useful extras

Most supplemental credit belongs to the target writing system itself. A broad
Unicode font cannot keep stacking points for every extra language it includes.
All three values below range from zero to one:

- **Depth, up to 8 points:** extended coverage within the target writing system.
- **Language, up to 1 point:** the strongest other-script coverage, not their sum.
- **Terminal, up to 1 point:** the lowest coverage of CP437, box drawing and block
  elements, so CP437 alone cannot imply a complete terminal symbol repertoire.

| Target | Depth reference |
| --- | --- |
| Simplified Chinese | Mean of GBK Han and 通用规范汉字表 |
| Traditional Chinese | Full Big5 |
| Japanese | Mean of JIS X 0208 level 2 and JIS X 0213 level 3 |
| Korean | All modern Hangul syllables |
| Latin | Mean of Latin-1 Supplement and Latin Extended-A |
| Cyrillic, Greek, Arabic, Thai | Their own reference chart; no separate extended chart exists in the catalogue |

The language bonus considers extended Latin, common Han, common Hangul,
Cyrillic, Greek, Arabic and Thai, excluding the target script. Basic Latin does
not earn an extra-language bonus. For this purpose all Simplified, Traditional
and Japanese Han references share one dimension (the highest common coverage),
and that dimension is excluded for all three Han targets. Their overlapping
repertoires cannot earn repeated cross-language credit.

At full main coverage and a preferred size, any of Latin, Simplified Chinese,
Traditional Chinese, Japanese or Korean can reach 98 points through its own
extended coverage alone. Another language and terminal symbols can contribute
only two more points together. Missing scripts are not separate penalties.
Partial extras earn proportional credit, and all extras scale with core
completeness: unrelated glyphs cannot rescue an unusable primary alphabet.
This automatic component has no font-specific exceptions. Aesthetic adjustments
are added separately after all automatic factors.

### Pixel size

For each native size `p`, let `d = max(8 − p, p − 16, 0)` and calculate
`sizeFactor = 1 − 0.12 × d / (d + 8)`. Use the best factor offered by the family.

| Size | Factor |
| --- | ---: |
| 3px | 95.38% |
| 7px | 98.67% |
| 8–16px | 100% |
| 17px | 98.67% |
| 24px | 94% |
| 32px | 92% |
| 64px | 89.71% |

Sizes outside the preferred range always decrease the factor as they get more
extreme, with a maximum reduction of 12%. A usable 12px strike remains useful
even when the family also offers 6px and 48px strikes. Duplicating strikes or
adding weights does not earn points. Sizes follow the same nominal native size
metadata as the size filter, not the glyph's ink bounds or its displayed zoom.

### License preference

The factors express this catalogue's small preference for ease of reuse. They
are editorial ranking weights, not legal compatibility judgments or a claim
that copyleft fonts are less open source.

| License | Factor | Maximum reduction from a 100-point coverage/size score |
| --- | ---: | ---: |
| Permissive licenses, public domain, CC0, OFL | 1 | 0 |
| GPL with a font exception | 0.985 | 1.5 points |
| CC BY-SA | 0.98 | 2 points |
| GPL / AGPL without a font exception | 0.96 | 4 points |

OFL has font-scoped copyleft, but ordinary document embedding and application
use do not place the document or application under OFL, so it remains at the
normal baseline. A GPL font exception addresses document embedding; it does not
remove the font's own copyleft. Sources: [OFL FAQ](https://openfontlicense.org/ofl-faq/)
and [GNU font exception](https://www.gnu.org/licenses/gpl-faq.en.html#FontException).

Read the actual catalogued SPDX identifier, including legacy
`GPL-2.0-with-font-exception` and standard `GPL-2.0-only WITH Font-exception-2.0`
forms. An unrelated exception is not treated as a font exception. For `OR`, use
the better factor, because the user may choose that license; for `AND`, use the
lower factor, because both apply. Parentheses and AND-before-OR precedence are
respected. For example, `OFL-1.1 OR GPL-2.0-with-font-exception` stays at 1, while
`MIT AND GPL-2.0-only` gets 0.96. Multiple obligations do not stack penalties.

Unknown, missing or malformed license metadata is neutral, not labelled
permissive. Inclusion and license verification remain separate from ranking.
Implementation: [licenserating.ts](../../site/src/lib/licenserating.ts).

### Manual aesthetic adjustments

The owner-selected preferences are stored by exact family slug in
[rating-adjustments.ts](../../site/src/lib/rating-adjustments.ts).
Unlisted families receive zero. These points are added once, after coverage,
size and license factors; changing them never changes the inferred target or
the automatic score. Positive adjustments are not clipped to 100, so already
complete fonts can still receive a useful bonus.

- **+0.5 points:** 秋叶圆体16.
- **+1 point:** Z工坊像素圆体, Z工坊像素黑体12px, 破晓像素, 目哉像素, 全小素.
- **+1.5 points:** 缝合像素 (Fusion Pixel), 俐方体11号, Ark Pixel, 精品点阵体,
  Galmuri, Misaki.

This is the complete adjustment list; there are no aesthetic deductions.
正格点黑16, Fusion Bold Pixel and Z Labs DiamondPix receive no adjustment.
The final score remains fixed across locales, reloads and filters.

### Google Fonts preference

The reviewed family list in [google-fonts.ts](../../site/src/lib/google-fonts.ts)
receives **+1 point** per family, after the automatic score and independently
of aesthetic adjustments. It covers all catalogue homepages on fonts.google.com
and the explicitly requested Tiny5, DotGothic16, Jersey and Jacquard families.
The current 13 families are Bitcount, Bytesized, DotGothic16, Doto, Handjet,
Jacquard, Jacquarda Bastarda 9, Jersey, Micro 5, Pixelify Sans, Press Start 2P,
Silkscreen and Tiny5. Multiple variants do not multiply the bonus. A test keeps
the list synchronized with homepage metadata. DotGothic16's aesthetic deduction
was removed on September 18 following its import correction.

## Stable ordering and limits

Round the score to six decimal places, sort descending, then use the ASCII slug
ascending to break ties. The calculation is identical in static HTML and the
browser. There is no seed, clock, locale-dependent tie-break or user history.
Filtering does not recalculate scores relative to the remaining candidates.
Legacy `sort=random` URLs fall back to Auto and normalize to the clean URL.

The automatic component does not award points for raw glyph count, variant
count, popularity, font age or visual style. Icon-only and restricted display
fonts may rank lower in this text-coverage sort; their categorical filters and
other sort options remain available. Visual preferences only enter through the
explicit manual adjustments above.

The CJK target threshold remains an inference rule: crossing from no CJK target
to an eligible one can change the primary evaluation from an alphabet to CJK.
Within the same candidate group, adding coverage cannot lower the score.

## September 18 automatic-score audit (before aesthetic adjustments)

The first formula used only the single strongest extra and gave 81 of the 412
families a perfect score. The revised automatic formula gave 11 families 100 points and
produced 173 distinct scores. Among the first 24 families, 11 had inferred CJK
targets and 13 have other targets. These are observations about the current
catalogue before manual adjustments, not quotas or inputs to the formula. Families with identical coverage,
size and license factors can still legitimately tie.

| Family | Coverage × size, before license | License factor | Automatic score |
| --- | ---: | ---: | ---: |
| Gohufont | 100 | 1 | 100 |
| WenQuanYi Bitmap Song | 99.305400 | 0.985 | 97.815819 |
| BestTen | 97.776800 | 1 | 97.776800 |
| WenQuanYi Unibit | 100 | 0.96 | 96 |
| DotGothic16 | 95.897200 | 1 | 95.897200 |
| Misaki | 94.384549 | 1 | 94.384549 |

Both WenQuanYi families complete common Chinese coverage at preferred sizes.
Unibit's more complete additional coverage earns a higher pre-license score.
Bitmap Song's recorded GPL font exception gives it a smaller license reduction
than Unibit's plain GPL, so the automatic ordering reverses. They ranked 76th and 129th
respectively before manual adjustments. This is the same general formula
used for every font, not a manual adjustment to separate those two families.
