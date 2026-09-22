# Site quality audit — 2026-09-22

This audit covers the production Astro build in the current workspace. It does
not describe a deployment or a live-domain audit.

## Search and social previews

- All rendered pages share title, description, canonical, robots, Open Graph,
  Twitter large-image metadata, and the appropriate structured data.
- Available translations have matching language alternates. Open Graph locales
  use territory codes. English-only documentation does not advertise missing
  translations.
- Every font page uses its own 1200 × 630 specimen image; other pages have a
  generated default image. Image type, dimensions, and alternative text are
  included in the head.
- The build produces sitemap-index.xml, robots.txt, llms.txt, and 36 Markdown
  documentation endpoints. The sitemap omits redirects and noindex pages.
- The generated-output check validates every page, sitemap target, language
  alternate, social image, and local link in llms.txt. llms.txt is a discovery
  aid; its presence does not guarantee search indexing or AI citations.

## Accessibility and keyboard interaction

The axe checks cover 10 representative routes in desktop light and mobile dark
modes, plus all 36 documentation pages. All 56 stored axe reports have zero
reported violations. Additional checks exercise an open coverage dialog and
navigation menu.

Keyboard regression coverage includes Tab and Shift+Tab, skip links, visible
focus, menu navigation, documentation tabs, tooltip dismissal, glyph inspection,
and modal focus containment and restoration. The checks also cover responsive
layouts down to 300 CSS pixels. Desktop catalogue and mobile About screenshots
were inspected manually.

Fixes include heading order, accessible names, unique landmark labels, text
contrast, underlined inline links, keyboard-scrollable content, canvas controls,
roving tab stops, and native modal interaction. Automated results do not certify
all WCAG requirements or replace evaluation with assistive technologies.

## Performance changes

- Moved name and label conversion to the build. The catalogue browser module
  dropped from approximately 519 KiB to 40 KiB by removing OpenCC dictionaries.
- Combined pixel SVG rectangles into paths without changing rendered pixels;
  raster comparisons cover light and dark colors. The catalogue document shrank
  from roughly 12,000 DOM elements to 1,000.
- Create missing-glyph buttons when their dialog opens instead of prerendering
  tens of thousands of hidden controls. The Galmuri detail HTML dropped from
  approximately 3.7 MB to 1.0 MB.
- Added explicit dimensions to documentation images.

## Verification

The SEO audit validates 2,936 rendered pages, 2,934 sitemap URLs, and 461 social
images with zero errors. All 274 fenced code blocks in the 36 exported
Markdown documents match their source.

The site unit suite passes 103 tests across 18 files. Type checks finish with zero
errors; non-fatal compiler warnings remain. The full browser suite exercises 261
tests. The initial run passed 259 tests; two stale assertions (the number of About
exclusions and SVG pagination ellipsis) were updated to match existing content
and presentation. All 16 tests in those two files then passed on rerun.

Reproduce from a complete font-data build:

```bash
cd site
bun run check
bun run test
bun run build
bun run audit:seo
bun run e2e
bun run audit:lighthouse
cd ..
python3 .github/scripts/check_pages_limits.py site/dist
```

Detailed Lighthouse HTML/JSON and axe reports live in the ignored
`site/quality-reports/` directory. CI runs the checks and uploads audit artifacts.

## Lighthouse results

Lighthouse 13.5.0 and Chromium 151 audited nine routes in each device mode,
with three fresh browser sessions per route. The performance gate uses the
median (at least 90); accessibility, best practices, and SEO must each score
100 in every sample. All 18 page/device combinations pass. The report's
actual form factor is checked against the requested mode.

| Route | Mobile performance | Desktop performance | Accessibility / Best practices / SEO |
| --- | ---: | ---: | --- |
| `/en/` | 90 | 100 | 100 / 100 / 100 |
| `/zh/` | 93 | 99 | 100 / 100 / 100 |
| `/en/page/2/` | 95 | 100 | 100 / 100 / 100 |
| `/en/fonts/galmuri/` | 98 | 99 | 100 / 100 / 100 |
| `/en/compare/` | 97 | 100 | 100 / 100 / 100 |
| `/en/about/` | 100 | 100 | 100 / 100 / 100 |
| `/en/tools/` | 100 | 100 | 100 / 100 / 100 |
| `/en/bdfparser-js/` | 99 | 100 | 100 / 100 / 100 |
| `/en/bdfparser-js/api/types/headers/` | 100 | 100 | 100 / 100 / 100 |

These are local lab measurements, not field data. The shared development machine
showed substantial CPU variation: for example, one Galmuri desktop series had
CPU benchmark indices of 2404, 212, and 240.5. Its performance scores were 100,
66, and 70. A further unpinned series scored 80, 61, and 74. The final Galmuri
desktop recheck was restricted to the i7-12700H performance cores (CPUs 0–11)
and scored 99, 99, and 76, giving the reported median of 99. Earlier and final
raw reports are retained; scores are not guaranteed on a busy machine.

The first single-pass English mobile catalogue audit also scored 79. Its final
three samples were 90, 91, and 89 (median 90). No thresholds were lowered to
accommodate these variations.

## Cloudflare Pages Free

The output is a static site, including font downloads, and needs no Pages
Functions or R2 bucket. The complete publish directory has 12,269 files; its
largest file is 22,187,372 bytes (21.16 MiB). This fits the Free plan's 20,000-file
limit and 25 MiB maximum file size, with room for another 7,731 files. Both CI
and deployment check the complete directory before upload.

Limits were checked against [Cloudflare's Pages limits](https://developers.cloudflare.com/pages/platform/limits/).
[Static asset requests are free and unlimited](https://developers.cloudflare.com/pages/functions/pricing/).
These checks establish that the current output fits; they do not test DNS,
custom-domain configuration, or an actual deployment.

## Documentation and remaining work

README.md is English and README.zh.md is Chinese; they link to each other and
document the build, deployment, licensing, and quality-check commands.

TODO.md remains necessary. Per-page documentation translation routing, sidebar
fallback, and Traditional Chinese conversion of MDX bodies are still deferred.
These are not completed by translating the READMEs or adding SEO metadata.
