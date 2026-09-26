"""Open-source pixel font collection build pipeline."""

# This version number is part of the cache key: any logic change that can
# alter output (engine decisions, formats, thresholds) must bump it, or a
# cache-hit family won't get rebuilt.
# Version of the site data contract: bump whenever index.json's shape
# changes, and update the matching constant in site/src/lib/schema.ts at
# the same time. The site compares versions on load and, on a mismatch,
# surfaces a "please rebuild" message to the developer instead of letting
# zod validation blow up into a stack trace.
DATA_SCHEMA_VERSION = 6  # Per-variant scripts and ink height in index.json; per-variant runs and coverage files.

# Version of the glyph pipeline: bump only when the built glyphs/coverage/TTF
# outlines would change; bumping it rebuilds every family (~10 minutes in
# parallel). Pure metadata logic (searchText, description fields, TTF name
# table, README) doesn't need it bumped — the cache-hit fast path
# recomputes those from current code every time.
PIPELINE_VERSION = 24  # v24: per-variant runs/coverage in the cache payload for same-variant filtering; v23: CJK scripts judged on core tables at 98%, kana and bopomofo sets narrowed
