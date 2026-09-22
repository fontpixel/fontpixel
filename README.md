# FontPixel.com: Open-source Pixel Fonts

**English** | [简体中文](README.zh.md)

A collection of freely licensed bitmap fonts. Put BDF or PCF files in `fonts/`
and the build produces a searchable static catalogue with per-glyph parsing,
nominal and ink measurements, coverage reports for more than 60 character sets,
pixel-exact previews you can type into, and downloadable font files.

- Website: [fontpixel.com](https://fontpixel.com/en/), available in six languages.
- Repository: [fontpixel/fontpixel](https://github.com/fontpixel/fontpixel).
- Documentation: [documentation index](docs/README.md) and [catalogue ranking](docs/specs/catalogue-rating.md).
- Inclusion criteria, measurements, and coverage methodology: the site's About page.

## Inclusion criteria

Only **freely licensed** fonts are included. The license must explicitly permit
use, copying, modification, redistribution, and commercial use. It must apply to
the exact files included here, with verifiable provenance. A label such as
“free,” “free for commercial use,” or “freeware,” permission to copy alone, or a
promise of a future open-source release is insufficient.

Each font retains its own license and associated conditions. Review decisions
and reasons for exclusions are recorded in [the import report](docs/import-report.md).

## Quick start

Requirements: Python 3.12+, Node.js 24+, Bun 1.4.2, and `bdftopcf` (on Debian or
Ubuntu, install `xfonts-utils`). Bun manages site dependencies; build tools run
on Node.js.

```bash
make setup    # Create the virtual environment and install dependencies
make test     # Run pytest and Vitest
make dev      # Build font data and start the development server
make build    # Build the production site in site/dist/
make e2e      # Run Playwright end-to-end tests
```

## Adding a font

Create a directory under `fonts/` containing BDF or PCF files; gzip-compressed
files are supported:

```text
fonts/my-font/
  my-font-16.bdf
  OFL.txt          # License text; common licenses are recognized automatically
  family.toml      # Metadata; missing metadata produces an uncatalogued stub
```

`forms` (multiple visual categories) and `vibes` (stylistic tags) are the main
fields recommended for manual curation. If the license cannot be recognized
automatically, provide its SPDX identifier, commercial-use status, and evidence
in the `[license]` section.

Use an array for categories, such as `forms = ["gothic", "decorative", "sans"]`.
`gothic` also includes `sans`; `song` also includes `serif`. Selecting several
categories matches any of them. Cards and detail pages display all categories.
Legacy single-value `form` metadata remains readable. Legacy values and filter
links such as `mingcho`, `round`, and `serif-pixel` are normalized to `song`,
`rounded`, and `serif` respectively.

`aliases` contains names of the same font: earlier names, upstream project
names, embedded font names, native-language names, and alternative word spacing.
Aliases are searchable but not displayed. Chinese aliases do not need separate
simplified and traditional entries; the build expands them. Names of fonts that
a family was derived from belong in `provenance`, not `aliases`.

Changing display metadata does not recompute glyphs. The cache depends on font
files and structural `family.toml` fields such as `merge`, `exclude`, `[variants]`,
`[license]`, and `name`; other changes use a quick metadata refresh. Full rebuilds
use up to eight worker processes by default, adjustable with `OPF_JOBS`. Use
`--family <slug>` to work on a single family.

## Bulk imports

`ingest/manifest.toml` maps upstream repositories to families. It supports ZIP
extraction, OTB and kbitx conversion, rasterization of vector pixel fonts on
their native grid, and inline `[family.license]` declarations.

```bash
.venv/bin/python -m opf.ingest.run \
  --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts \
  --dest fonts --report docs/import-report.md
```

`--report` rewrites only the generated section before the `<!-- opf:manual … -->`
marker. Manual records after it, including licensing decisions and removals,
remain intact. If an existing report lacks the marker, the importer refuses to
overwrite it.

Shinonome has a separate importer because upstream distributes `.bit` sources:

```bash
.venv/bin/python -m opf.ingest.shinonome --repo <shinonome-repository> --dest fonts
```

## Downloads

- **BDF** (`.bdf.gz`) and **PCF** (`.pcf.gz`): original bitmap formats, per variant.
- **Bitmap TTF**: all sizes of the same weight, spacing, and language subset in
  one file, using EBDT/EBLC strikes and empty `glyf` outlines. These work on
  systems that support embedded bitmap strikes.
- **Vector TTF and WOFF2**: square and rounded pixel outlines, where generated.
- **Family ZIP**: BDF files, license text, and provenance notes.

## Search

Search recognizes equivalent simplified and traditional Chinese names in both
directions. Equivalence classes come from Unicode Unihan's `kSimplifiedVariant`
and `kTraditionalVariant` data. The build expands the search index, so browsers
do not need to download the conversion tables.

## Architecture and deployment

```text
fonts/               Font sources tracked in Git
pipeline/            Python parsing, metrics, coverage, licensing, previews,
                     downloads, and JSON indexes
site/                Astro 5 static site with Svelte interactions
site/public/data/    Generated data and previews, ignored by Git
dist-downloads/      Font downloads copied into the site's /downloads/ directory
```

GitHub Actions builds and deploys one Cloudflare Pages project containing both
the website and font downloads. Default previews use SVG; interactive previews,
comparison, and glyph browsing share BDF downloads parsed and cached in a Web
Worker. There is no second set of published glyph chunks. BDF exports use
Unicode encoding and preserve bitmaps, metrics, and unencoded alternative
glyphs. Original upstream files in `fonts/` remain unchanged.

`bun run build` prepares the download directory automatically. Before deployment,
run `python .github/scripts/check_pages_limits.py site/dist` to check the full
output against Cloudflare Pages Free limits: 20,000 files and 25 MiB per file.
The current architecture needs neither a second Pages project nor R2. `OPF_BASE`
sets the deployment path; `OPF_SITE` sets the canonical origin and defaults to
`https://fontpixel.com`.

The catalogue has 24 fonts per page, using real static URLs such as
`/en/page/2/`. All six languages share the same default order. Every page renders
font links, SVG previews, and pagination links without requiring JavaScript.
Filtering preserves relative order and returns to page one. Sorting by name,
size, or glyph count is also available.

The default Auto ranking mainly reflects completeness in a font's primary
writing system: 90 points for core coverage, eight for extended coverage, and up
to one each for other scripts and terminal symbols. Coverage across writing
systems does not accumulate, and overlapping Chinese and Japanese characters
are not counted twice. Native sizes outside 8–16 pixels receive a gradual,
small reduction. License adjustments reduce GPL with a font exception by 1.5%,
plain GPL by 4%, and CC BY-SA by 2%; OFL and permissive licenses keep the baseline.
License expressions respect OR choices and simultaneous AND requirements.

Curated preferences add 0.5, one, or 1.5 points to selected families, configured
in `site/src/lib/rating-adjustments.ts`. Families on the list in
`site/src/lib/google-fonts.ts` receive one additional point. Scores can exceed
100. CJK ranking uses common-character lists and a more forgiving coverage curve,
without requiring all of Unicode. Ties are resolved by family slug, keeping the
order stable across refreshes, languages, and rebuilds. See the
[ranking specification](docs/specs/catalogue-rating.md) for details.

The default preview chooses the variant with the most glyphs among sizes from
8 to 16 pixels, inclusive. If none qualify, it chooses from all sizes.
`default_variant` in `family.toml` overrides that choice. Both full builds and
cached refreshes use the same deterministic selection rules.

## SEO, accessibility, and quality checks

The static build generates `robots.txt`, a multilingual sitemap, `llms.txt`,
Markdown documentation endpoints, and a default social preview image. Pages
share canonical URLs, language alternates, Open Graph and Twitter metadata, and
structured data; individual font pages use their own specimen images.

```bash
cd site
bun run check              # Astro, TypeScript, and Svelte checks
bun run build              # Build production output before audits
bun run audit:seo          # Check every generated page and sitemap entry
bun run test:a11y          # axe audits and keyboard interaction regressions
bun run audit:lighthouse   # Mobile and desktop Lighthouse reports
```

Lighthouse reports are stored in `site/quality-reports/`. Performance is checked
against a median score of 90 across three cold-cache runs; accessibility, best
practices, and SEO must score 100 in every run on the representative pages.
Automated audits complement keyboard testing and do
not replace evaluation with assistive technologies.

See the [2026-09-22 audit](docs/audits/site-quality-2026-09-22.md) for the tested
scope and results.

## Licenses

- Repository code: MIT; see [LICENSE](LICENSE).
- Fonts: their respective licenses, included in each family directory and detail page.
- Character-set and variant data: see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
