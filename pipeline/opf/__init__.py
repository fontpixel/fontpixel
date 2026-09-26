"""Open-source pixel font collection build pipeline."""

# This version number is part of the cache key: any logic change that can
# alter output (engine decisions, formats, thresholds) must bump it, or a
# cache-hit family won't get rebuilt.
# Version of the site data contract: bump whenever index.json's shape
# changes, and update the matching constant in site/src/lib/schema.ts at
# the same time. The site compares versions on load and, on a mismatch,
# surfaces a "please rebuild" message to the developer instead of letting
# zod validation blow up into a stack trace.
DATA_SCHEMA_VERSION = 5  # Per-variant CJK set and intersection coverage in detail.json.

# Version of the glyph pipeline: bump only when the built glyphs/coverage/TTF
# outlines would change; bumping it rebuilds every family (~10 minutes in
# parallel). Pure metadata logic (searchText, description fields, TTF name
# table, README) doesn't need it bumped — the cache-hit fast path
# recomputes those from current code every time.
PIPELINE_VERSION = 23  # v23: CJK scripts are judged on core tables (tongyong level 1, Taiwan chart A, JIS kana + level 1, KS X 1001 hangul) at 98%; kana and bopomofo sets narrowed
