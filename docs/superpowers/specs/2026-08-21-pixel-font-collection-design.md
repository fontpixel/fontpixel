# Open Pixel Fonts (开源像素字体馆) — Design Specification

Date: 2026-08-21
Status: confirmed section by section with the project owner
Site name: Open Pixel Fonts / 开源像素字体馆
Deployment: GitHub Pages (presentation assets) + GitHub Releases (downloadables)

## 1. Background and Goals

Turn the collected open-source bitmap fonts (mostly CJK) into an automatically built static catalogue site. A font source is included automatically once its BDF/PCF is placed in the `fonts/` directory. The old project `../open-pixel-fonts-old` is scrapped and redone in full; its coverage-report concept is kept and substantially extended, while visuals, interaction, and engineering all start over. The three confirmed failings of the old project: the visuals had an AI smell, interaction and features were inadequate, and engineering quality was poor (including hash routing, which is bad for sharing).

**Success criteria**

- Every imported family builds reproducibly, with complete artifacts (glyph packs, prerenders, downloadables, indexes).
- Site Pages payload ≤ 900MB (hard CI check); catalogue page first-screen JS < 150KB gz.
- For every font family: complete attributes, a complete coverage report, an editable sample, and downloadable BDF/PCF.
- Visuals that survive a picky eye: not template-like, not AI-generated-looking.
- Fully usable in both Chinese and English.

**Inclusion criteria (tightened 2026-08-29)**

Only libre-licensed fonts are included: the license must explicitly permit use, copying, modification, and redistribution **and permit commercial use**,
must explicitly apply to the very file being included, and the provenance chain must be verifiable. A mere "free", "free for commercial use", or "freeware"
label, or a license that only permits copying, does not count; nor does an author's not-yet-executed promise to "switch to an open license later".

**Non-goals (not in v1)**

- Backend, accounts, comments, user uploads.
- OTF/WOFF2 download distribution (for converted sources, link upstream to the original vector font instead of redistributing it).
  Note: bitmap TTF was added on 2026-08-29, see §4.7 — it carries bitmap strikes and contains no vector outlines, which is not the same thing as the vector distribution excluded here.
- Color fonts, emoji, vertical samples.

## 2. Confirmed Key Decisions

| Decision point | Conclusion |
|---|---|
| Import scope | Native bitmap formats (BDF, BDF inside a zip, OTB, kbitx, FNT case by case) taken directly; vectorized pixel TTF/OTF/woff2 rasterized and converted into BDF with a note; PNG image sources / C header files evaluated one by one, skipped when redundant |
| Deployment | GitHub Pages; downloadables published via a rolling GitHub Release |
| Languages | Chinese and English, dual routes `/zh/` (default) and `/en/` |
| Catalogue unit | The real font family (split at import time, e.g. baekmuk split into 4 families) |
| Source policy | `fonts/` sources (BDF + metadata + license) go into the main repo's git; generated artifacts do not |
| Style system | Two layers: a controlled "letterform category" plus free-form "vibe tags", both filterable |
| Site architecture | Astro 5 SSG + Svelte 5 islands + TypeScript |
| Sample rendering | Direct canvas bitmap drawing (binary glyph chunks) + build-time SVG prerender for SEO / no-JS |
| Build pipeline | Python 3.12 (fonttools, freetype-py), covered by pytest |

## 3. Repository and Directory Conventions

```
open-pixel-fonts/
├── fonts/                        # font sources, git-tracked
│   └── <family-slug>/
│       ├── family.toml           # hand-written metadata (optional; builder generates a stub)
│       ├── LICENSE / OFL.txt …   # upstream license text
│       └── *.bdf | *.bdf.gz | *.pcf | *.pcf.gz   # one file = one variant
├── pipeline/                     # Python build pipeline
│   ├── build.py                  # entry point: fonts/ → artifacts
│   ├── parsers/                  # bdf.py pcf.py otb.py kbitx.py
│   ├── coverage/                 # coverage computation + data/ charsets (versioned, with provenance notes)
│   ├── metrics.py                # claimed / ink metrics
│   ├── licenses.py               # license detection
│   ├── glyphpack.py              # glyph pack writer
│   ├── prerender.py              # SVG samples + og:image PNG
│   ├── downloads.py              # bdf.gz / pcf.gz / family zip + manifest
│   └── ingest/                   # import tooling (see §6)
├── site/                         # Astro project
│   ├── src/pages/                # routes (including [lang])
│   ├── src/islands/              # Svelte islands
│   ├── src/lib/                  # glyph pack decoder, GlyphStore, filter logic (vitest)
│   └── public/data/              # pipeline artifacts (gitignored)
├── dist-downloads/               # downloadables (gitignored, uploaded to Releases by CI)
├── docs/superpowers/specs/       # design and plan documents
└── .github/workflows/build.yml
```

### 3.1 family.toml

Only fill in fields a machine cannot infer; when it is missing, the builder generates a stub with TODO comments and the site marks the family "uncurated".

```toml
name = "Galmuri"                  # required (stub derives it from the directory name)
name_zh = ""                      # optional, Chinese display name
author = "quiple"
homepage = "https://galmuri.quiple.dev"
repository = "https://github.com/quiple/galmuri"
description = ""                  # optional, one-line blurb (Chinese; English produced by the translation flow)
form = "gothic"                   # controlled letterform category, see §3.3; empty = "uncategorized"
vibes = ["retro-game"]            # free-form vibe tags (kebab-case; the site aggregates them into filters)
converted_from = ""               # conversion source: "ttf"|"otf"|"woff2"|empty = native
provenance = ""                   # source and acquisition notes (written automatically by the import tool)

[license]                         # omit the whole block when auto-detection succeeds
spdx = "OFL-1.1"                  # or LicenseRef-<name>
name = ""                         # display name for a custom license
file = "OFL.txt"                  # points at a text file in the directory
note = ""                         # additional restriction notes

[samples]                         # optional, overrides the default sample sentence
zh-Hans = "…"

[variants."Galmuri11.bdf"]        # optional, per-variant overrides
display = "Galmuri 11"
weight = "regular"                # regular|bold|light|…
spacing = "proportional"          # monospaced|proportional
script_subset = ""                # zh-Hans|zh-Hant|ja|ko|latin|… (fusion-pixel style subsetting)
```

### 3.2 Variant Model

Variant dimensions = claimed size × weight × monospaced/proportional × language subset. Auto-detection priority: BDF/PCF properties (`PIXEL_SIZE`, `WEIGHT_NAME`, `SPACING`, `CHARSET_REGISTRY`, etc.) → filename heuristics → manual `[variants]` overrides. The family page organizes variants with size as the primary axis and the rest as switchers.

### 3.3 Controlled Letterform Categories (form)

`gothic` heiti/gothic sans, `mingcho` songti/mincho serif, `rounded` rounded, `kai` kaishu, `fangsong` fangsong, `songti-serif` serif pixel (Latin serif lineage), `sans` sans-serif pixel (Latin), `script` handwriting, `decorative` decorative/display, `terminal` terminal/system, `other` other. The vocabulary may be extended or trimmed during implementation, but stays controlled (the site's filter lists each entry with bilingual names). One primary category per family, with at most one secondary category allowed.

## 4. Build Pipeline

Flow: scan → parse → metrics → coverage → license → artifacts (glyph packs / prerenders / downloadables / indexes). The whole flow is incrementally cached on "file content hash + pipeline version" (`.cache/`, gitignored).

### 4.1 Parsers

- **BDF**: full property table, per-glyph `ENCODING` (those ≥0 enter the encoding table), `BBX`, `DWIDTH`, bitmap. Tolerates common dialects (duplicate properties, non-standard lines) and records build warnings.
- **PCF**: the properties, metrics, ink metrics, bitmaps, encoding, and glyph names tables, handling byte order / bit order / scan unit. Non-Unicode encodings (ISO 8859, GB2312, JIS, KS, Big5, etc.) are mapped to Unicode; anything that cannot be mapped reliably produces a warning shown on the site.
- **OTB**: fonttools reads `EBDT/EBLC` (converted to BDF on disk at import time; the site pipeline consumes only BDF/PCF).
- **kbitx / FNT**: same as above, used only at import time.

### 4.2 Metric Definitions (published on the site's About page)

- **Claimed size**: `PIXEL_SIZE` → `SIZE` (pt@dpi conversion) → `FONTBOUNDINGBOX` height, rounded to whole pixels.
- **Han ink size**: take the intersection with Level 1 of the Table of General Standard Chinese Characters that the font actually covers (falling back to all CJK Unified Ideographs when fewer than 100 characters are available), compute each glyph's actual lit-pixel bounding box, take the median of width and of height separately, and report it as "W×H". For fonts without Han characters, report instead: the median ink height of uppercase A–Z (cap height), the lowercase x-height, and the largest ASCII ink box.
- **Whole-font maximum ink**: the maximum ink width/height across all glyphs, recording the code points that hit the extremes (combining marks and extra-wide PUA glyphs can push this beyond the claimed box, which is normal; the page carries a footnote).
- Also collected: ascent/descent, `FONTBOUNDINGBOX`, DWIDTH distribution (monospace test: ≥99% of glyphs sharing one width counts as monospaced, cross-checked against the `SPACING` property).

### 4.3 Coverage Computation

The set of code points in the encoding table (a bitset) is tallied against each charset in §7. Counting rules: one code point counts once; the denominator is the number of code points in the versioned data file; compatibility ideographs and unified ideographs are listed separately, with the twelve "actually unified" characters FA0E/FA0F/FA11/FA13/FA14/FA1F/FA21/FA23/FA24/FA27/FA28/FA29 footnoted separately. Coverage is computed per variant; family-level filtering uses "any variant meets the threshold".

### 4.4 License Detection

Three confidence levels:

1. **auto-high**: `LICENSE*`, `LICENCE*`, `COPYING*`, `OFL*` in the directory plus any license text found by scanning, whitespace-normalized and matched against known full-text fingerprints. First batch of fingerprints: OFL-1.1, OFL-1.0, MIT, Apache-2.0, GPL-2.0/3.0 (including Font Exception variants), LGPL-2.1, CC0-1.0, CC-BY-4.0, CC-BY-SA-4.0, WTFPL, Unlicense, IPA Font License 1.0, M+ Font License (old version), Baekmuk License, public-domain declarations.
2. **auto-low**: only a hint from the BDF `COPYRIGHT`/`NOTICE` properties; the site displays "unconfirmed".
3. **manual**: `family.toml` `[license]` overrides everything.

Unrecognized → build warning + a "license unconfirmed" banner on the site. (The former `commercial` field was removed on 2026-08-31: the inclusion criteria already require the license to permit commercial use, so no non-commercial font exists on the site, and recording a per-font field that is always true is redundant — it had also mis-reported "unknown" because the whitelist was incomplete.) Site-wide footnote: license information is for reference only; the upstream original text governs.

### 4.5 Glyph Packs (the data source for canvas rendering)

- One manifest JSON per variant (range → chunk file, byte count, glyph count, sha256) plus a number of binary chunks, stored gzipped (`.bin.gz`) and decompressed on the front end with `DecompressionStream('gzip')`.
- Chunks are split by code point range, targeting ≤ 16KB gzipped per chunk, and support random access by code point (in-chunk index: code point → metrics + bitmap offset; metrics include DWIDTH and the BBX quadruple).
- Each variant also gets a **core pack**: printable ASCII + hiragana/katakana + Hangul Compatibility Jamo + every character used in the default sample sentences + the characters of the family display name, targeting ≤ 8KB gz; a catalogue card (name + sample line) can be rendered from the core pack alone, and only editing the sample triggers chunk fetches.
- The exact binary layout (magic number, version, field widths) is fixed during implementation together with the decoder tests; the spec requires backward compatibility within version v1 and a dependency-free pure-TS decoder.

### 4.6 Prerendering and Social Cards

- Each family's default sample is rendered at build time into inline SVG (horizontally contiguous pixels merged into rects to keep the node count down) and written into the static HTML: visible without JS, indexable for SEO; once JS is ready it is seamlessly replaced by an editable canvas.
- One og:image PNG per family (drawn with Pillow, containing the site name and a sample of the family name).

### 4.7 Downloadables and Releases

- Per variant: `<family>--<file>.bdf.gz`, `<family>--<file>.pcf.gz` (generated by bdftopcf; a conversion failure is recorded as a warning and only BDF is offered). Per family: `<family>.zip` (all variant BDFs + license + a README describing provenance).
- **Bitmap TTF** (added 2026-08-29): grouped by (weight × spacing × language subset), with all pixel sizes in a group packed into one TTF, carried as EBDT/EBLC strikes, with empty outlines in `glyf` and no vector data. Filenames carry only the dimensions that actually differ between groups (a single-group family is simply `<family>.ttf`). Implementation in `pipeline/opf/ttfexport.py`, verified by "build → read back with the OTB parser → compare byte for byte against the source BDF".
- CI uploads to a rolling Release (tag `downloads`), replacing only the assets whose manifest sha256 changed; site links point at `releases/download/downloads/<asset>` and display file size and sha256.
- Local dev: links point at the local `dist-downloads/` (statically mounted by the dev server); production switches the base URL via an environment variable.

### 4.8 Index Artifacts

- `index.json` (catalogue page, target ≤ 50KB gz): per family, slug, bilingual names, form/vibes, size list, weights, monospaced-ness, writing systems, license (spdx), key coverage summary, Han ink and claimed sizes, glyph count, author, whether converted, core pack and prerender paths, variant list.
- Per-family `detail.json`: the full coverage tree (per variant), all metrics, build warnings, download manifest.
- `coverage-intervals.bin.gz`: the covered code point ranges for all families (family-level union), loaded once on demand for the character-lookup feature and missing-glyph highlighting.

## 5. Site Information Architecture

Routes (`ASTRO_BASE` configurable, default `/open-pixel-fonts`):

- `/` — a minimal page that redirects to zh/en based on `navigator.language`, with hreflang.
- `/zh/`, `/en/` — the catalogue page (i.e. the home page).
- `/{lang}/fonts/<slug>/` — family detail page.
- `/{lang}/about/` — About: inclusion criteria, methodology for metrics and coverage, charset sources and acknowledgements, contribution guide (how to add a font / write family.toml), license disclaimer.
- `/404.html` — a 404 rendered with fonts from the collection.

### 5.1 Catalogue Page

- Toolbar: full-text search (name/author/tags; **simplified–traditional interchange** — searching 东云 matches 東雲, with variant-character equivalence classes expanded into `searchText` at build time from the Unihan `kSimplifiedVariant`/`kTraditionalVariant` fields, so the front end needs no mapping table), a **global sample text box** (redraws as you type, applied to every card), pixel zoom ×1/×2/×3, and invert (black on white / white on black).
- Filters (all serialized into the URL query so they can be shared): letterform category, vibe tags, claimed size (discrete px chips), Han ink height (range), writing system, license (multi-select SPDX; the "commercial use only" toggle was removed on 2026-08-29 — the inclusion criteria were tightened to strict libre licensing, so every font permits commercial use and the filter no longer means anything), monospaced/proportional, weight, native/converted, coverage threshold presets (GB2312 ≥99%, Frequently Used Chinese Characters (TW) ≥99%, JIS Level 1 ≥99%, kana 100%, KS X 1001 Hangul ≥99%, plus a custom "pick any charset + threshold"), and **character lookup** (type any characters and only fully covering families are shown).
- Sorting: name / claimed size / glyph count / recently added.
- Cards: the family name self-rendered in that font + a sample line on canvas (following the global sample, lazily rendered via IntersectionObserver) + metadata chips (size, category, license, writing system, glyph count, converted badge, uncurated badge). Characters the font lacks appear in the sample as a placeholder box with a highlight.
- Virtual scrolling once the family count exceeds what the viewport can carry (decided by measurement during implementation; expected to be needed at roughly 100+ families).

### 5.2 Family Detail Page

- Header: family name self-rendered at large size, author/homepage/repository/source, license badge (confidence visible, full text collapsible), form/vibes, conversion notes (where applicable).
- Variant switching: size as the primary axis + weight / monospacing / language-subset switchers.
- **Editable sample**: multi-line input, per-script preset sentences, zoom, invert, gridline toggle, and a **missing-glyph highlight** toggle. Default sentences: zh-Hans "天地玄黄,宇宙洪荒。日月盈昃,辰宿列张。"; zh-Hant "落霞與孤鶩齊飛,秋水共長天一色。"; ja "色は匂へど 散りぬるを 我が世誰ぞ 常ならむ"; ko "다람쥐 헌 쳇바퀴에 타고파"; latin "Sphinx of black quartz, judge my vow. 0123456789". A family defaults to the sentence for its primary writing system; `[samples]` can override it.
- **Claimed vs. ink visualization**: a small diagram overlaying the claimed box and the ink box of a representative Han character, with numeric labels.
- **Glyph grid browser**: a virtually scrolled grid with jump-to-Unicode-block navigation; clicking a glyph opens an inspector (magnified bitmap, code point, glyph name, BBX/DWIDTH/ink box). Data is lazily fetched chunk by chunk according to scroll position.
- **Coverage report**: the eight sections of §7, with progress bars drawn as discrete pixel squares; switchable per variant; each row shows name (bilingual), n/denominator, percentage, and a source tooltip; rows with ≤ 500 missing characters can be expanded to view the missing-character list (rendered as copyable text).
- Download area: per-variant BDF/PCF (labelled with size and sha256) + the family zip; converted families also carry a link to the upstream vector font.
- Metrics area: a table of every value collected in §4.2.

### 5.3 Client-Side Data Flow

A singleton GlyphStore (TS): manifest cache + chunk LRU + on-demand fetch; shared by the catalogue and detail pages. Filter logic is written as pure functions (covered by vitest). `coverage-intervals.bin.gz` is loaded only when character lookup is triggered.

## 6. Import Tooling (pipeline/ingest)

Usable both for the one-off bulk run and for future incremental additions. Input `../pixel-font-collection-fonts/`, output `fonts/` family directories plus an import report.

- **Mapping manifest** `ingest/manifest.toml` (maintained by hand, with a first draft generated by code): source path → target family (including splits, e.g. `chocolatemelt--baekmuk` → `baekmuk-batang`/`baekmuk-dotum`/`baekmuk-gulim`/`baekmuk-hline`; `RELEASE-ASSETS/*.zip` → unpack and take the BDFs).
- **Source priority**: official release BDF > in-repo BDF > OTB/kbitx conversion > TTF rasterization. When the same font appears in several places, the highest priority wins and the duplicates are recorded in the report.
- **TTF/OTF/woff2 conversion**: freetype-py rasterizes at the native grid ppem (monochrome mode). Native ppem detection: the GCD of the outline coordinate grid / divisibility against the em, plus metadata, cross-checked by rendering representative characters; families where detection fails go into the report for manual handling. Converted families get `converted_from` and `provenance`.
- **License and provenance**: license text is copied from the source directory; `provenance` records the source URL, acquisition date, and conversion method.
- **Skip policy**: PNG image sources, C header files, u8g2 binaries, and the like are skipped when the same font already has another usable source; those with no source at all go onto the report's "to be decided" list and are decided one by one.
- **Idempotence**: reruns produce no duplicates; a target directory that already exists with a matching hash is skipped.
- **Report** `docs/import-report.md`: inclusion list, split decisions, dedup records, skips and reasons, items needing manual work (including the style-annotation to-do list, prefilled with suggested values and marked "unverified").

## 7. Coverage System (Eight Sections)

For every charset: bilingual name, source and version, a one-line purpose note (tooltip), and a denominator taken from a versioned data file under `pipeline/coverage/data/` (each file's header states source, version, acquisition date, and license). Data from the old project's `scripts/data/cjk-tables/` (derived from CJK-character-count, MIT) is migrated and reused, then filled out per the list below; third-party data is acknowledged in `THIRD_PARTY_NOTICES.md`.

1. **Overview**: total encoded characters (denominator: everything assigned in Unicode 17.0), distribution by plane (BMP/SMP/SIP/TIP/SSP), the three PUA areas (BMP PUA / Plane 15 / Plane 16), total Han characters (URO + Extensions A–J), compatibility ideographs (including the supplement block, with the 12-character footnote).
2. **Simplified · national standards**: GB/T 2312-1980 (Level 1 3755 / Level 2 3008 listed separately), GB/T 12345-1990, GBK Han characters, GB 18030-2022 implementation levels 1 / 2 / 3.
3. **Simplified · language standards**: Table of General Standard Chinese Characters 2013 (Level 1 3500 / Level 2 3000 / Level 3 1605 listed separately), List of Frequently Used Characters in Modern Chinese (frequently used 2500 / less frequently used 1000), List of Commonly Used Characters in Modern Chinese 7000, Compulsory Education Chinese Curriculum Frequently Used Character List 3500, Standard Glyph Table of Common Characters for Ancient Book Printing, Kangxi Radicals 214, CJK Radicals Supplement 115; with vendor-defined lists appended at the end: the Hanyi simplified/traditional character list and the Founder simplified/traditional character list.
4. **Traditional · Taiwan**: Standard Typefaces for Frequently Used Chinese Characters 4808, Standard Typefaces for Less Frequently Used Chinese Characters 6343, Big5 (frequently used 5401 / less frequently used listed separately), Bopomofo (including extensions).
5. **Traditional · Hong Kong**: List of Graphemes of Commonly-Used Chinese Characters 4825, HKSCS-2016.
6. **Japanese**: JIS X 0208 (non-kanji / Level 1 2965 / Level 2 3390 listed separately), JIS X 0213 Levels 3 and 4, Jōyō kanji 2136, Kyōiku kanji 1026, Jinmeiyō kanji, hiragana, katakana, halfwidth kana, JIS X 0201.
7. **Korean**: KS X 1001 (Hangul syllables 2350 / hanja 4888 / symbols), all 11172 modern Hangul syllables, Hangul Compatibility Jamo, Hangul Jamo.
8. **General and international**: IICore 9810, UnihanCore2020, CJK Unified Ideographs Extensions A–J block by block, WGL4 652, Latin (Basic / Latin-1 Supplement / Extended-A/B), Greek and Coptic, Cyrillic (basic + extended), the Vietnamese Latin character set, CP437, Box Drawing, Block Elements, Powerline symbols (U+E0A0–E0D4), Braille, and a collapsible master table of **every Unicode 17.0 block** (showing only non-zero blocks by default).

Catalogue cards automatically pick which "meets threshold" badges to show based on writing system (e.g. GB2312 ✓, Big5 ✓, JIS1 ✓, KS X 1001 ✓, kana ✓).

## 8. Visual Direction

Concept: **a specimen hall** — the fonts are the exhibits, the interface is the glass case.

- Near-monochrome: paper white (light) / charcoal (dark) dual themes, with a single accent color, **cinnabar red**; no tech blue, no gradients, no glassmorphism, no page-wide large corner radii.
- UI text uses the system font stack (PingFang / Noto Sans CJK stack for Chinese, system-ui for Latin); **the site name and page headings are self-rendered in collection fonts**, so the pixel styling stays a finishing touch.
- Bitmap echoes in the details: coverage progress bars made of discrete pixel squares; 1px solid or dotted rules; numerals set in monospaced/tabular figures.
- A strict typographic grid with generous whitespace; full dark theme support (with the canvas inverting in step).
- The frontend-design skill is loaded during implementation to polish the concrete visuals; the principles in this section are the acceptance baseline.

## 9. Engineering, Testing, and CI

- **Stack**: Python 3.12 (pyproject; uv when available, otherwise venv+pip; depends on fonttools, freetype-py, Pillow), Node 24, Astro 5, Svelte 5, TypeScript strict.
- The catalogue page's "ink height" filter uses Han ink height; families without Han characters fall back to cap height on the same filter axis.
- **Testing**:
  - pytest: golden samples for each parser (a small hand-built BDF plus PCF fixtures generated by bdftopcf), metric definition cases, coverage counting cases, license fingerprint cases, glyph pack writer round-trip.
  - vitest: the glyph pack decoder (sharing binary fixtures with the Python writer), the pure filter functions, GlyphStore.
  - Playwright smoke tests: catalogue page rendering, filtering, sample editing triggering a redraw, the detail page's glyph grid, download links validated against the manifest.
  - TDD throughout implementation (the superpowers flow).
- **CI (GitHub Actions)**: job1 pipeline (cached on the fonts/ hash) → job2 Astro build + size red-line check (≤900MB) → Pages deployment; job3 incremental upload of downloadables to Releases. PRs only run the build and tests, without deploying.
- **Licensing**: code is MIT; fonts keep their own licenses; charset data carries third-party notices.
- **i18n**: typed zh/en dictionaries for UI copy; charset names and descriptions are bilingual and travel with the data files. **All English translation is done by Opus/Sonnet subagents (global rule: Fable does not do translation directly, including translation review).**

## 10. Implementation Order

1. **Pipeline core**: BDF parsing → metrics → coverage (Overview + GB2312 first) → glyph packs + decoder.
2. **Site skeleton**: Astro + catalogue page + detail page, with 5 pilot families proving out the end-to-end path (ark-pixel, galmuri, the four baekmuk splits, UnifontEX as a stress test, and one TTF-converted family).
3. **Fill-out**: PCF parsing, all coverage sections, license detection, prerender/og, downloadables + Releases, character lookup, glyph grid.
4. **Bulk import**: run ingest over the whole collection folder, produce the import report; hand the style-annotation list to the owner for review.
5. **Visual polish + bilingual copy + CI/deployment go-live.**

Per-stage completion criteria and task breakdown are in the subsequent implementation plan (writing-plans).

## 11. Risks and Agreed Handling

- **Pages payload**: glyph packs are estimated at 100–200MB total (gzipped), leaving headroom; if the limit is exceeded, first make rare chunks outside the SMP load on demand, then consider secondary hosting on a Release.
- **Legacy PCF encoding mapping**: fonts that cannot be mapped reliably are shown in degraded form with a warning, without blocking the build.
- **TTF native grid misdetection**: a failed check means no automatic conversion; the case goes into the report for a manual decision.
- **Release asset URL stability**: asset names contain the family slug and no hash, so links stay stable long-term; content changes are expressed through the manifest sha256.
- **Build duration**: incremental caching + parallel parsing; target for a full cold build < 15 minutes (in CI).
