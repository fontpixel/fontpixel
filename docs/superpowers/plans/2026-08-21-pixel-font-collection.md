# Open Pixel Fonts (开源像素字体馆) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A bilingual static bitmap-font catalogue site built automatically from the `fonts/` directory, with coverage reports, canvas pixel samples, BDF/PCF downloads, and bulk import tooling.

**Architecture:** A Python pipeline (parse BDF/PCF → metrics/coverage/licenses → binary glyph packs + SVG prerenders + downloadables + JSON indexes) emits into `site/public/data/`; an Astro 5 SSG bilingual site consumes that data through Svelte 5 islands and renders samples pixel by pixel on canvas; downloadables are uploaded to GitHub Releases by CI.

**Tech Stack:** Python 3.12 + fonttools + freetype-py + Pillow + pytest; Node 24 + Astro 5 + Svelte 5 + TypeScript strict + vitest + Playwright; bdftopcf.

**Spec:** `docs/superpowers/specs/2026-08-21-open-pixel-fonts-design.md` (this plan argues from that spec; implementers read both)

> **Progress (2026-08-21)**: Tasks 1–21 are complete and were each committed individually; Task 24 (CI/README) is complete;
> Task 22 is in progress (the five pilot families are live, and the full list is being drafted by a parallel agent); Tasks 23 and 25 remain.
> The per-task commit history is the tracking record (git log --oneline).

## Global Constraints

- Site Pages artifacts ≤ 900MB (hard check in the build script); catalogue page first-screen JS < 150KB gz.
- Core pack ≤ 8KB gz per variant; chunks target ≤ 16KB gz, with a 48KB raw ceiling.
- All UI copy is written in Chinese first; **English translation is always produced and reviewed by Opus/Sonnet subagents (global rule; Fable must not translate directly)**.
- TDD: write the failing test first for every feature; commit format `<type>: <short summary>` (feat/fix/test/docs/chore/refactor).
- Charset data files must carry a header comment: source, version, acquisition date, license; third-party data is registered in `THIRD_PARTY_NOTICES.md`.
- Pipeline determinism: same input, same output (lexicographic traversal, fixed gzip mtime=0); incremental cache key = file sha256 + PIPELINE_VERSION.
- Python package name `pfc` (under `pipeline/`, `pip install -e pipeline`); site library code in `site/src/lib/`.
- The site base path is configurable (`OPF_BASE`, default `/open-pixel-fonts`); every fetch goes through `withBase()`.
- Old project code is reference only, never copied; the old project's `scripts/data/cjk-tables/*.txt` data files may be migrated (MIT, notice retained).

---

## Shared Contracts (the authoritative definitions for all tasks)

### C1. Glyph pack binary format v1 (little-endian)

One file = one chunk, covering the code point range `[rangeStart, rangeEnd)`. The core pack uses the same format with the range `[0, 0x110000)`, stored sparsely. Written to disk gzipped (`.bin.gz`, mtime=0).

```
Offset  Type  Field
0       4B    magic = "PFG1"
4       u8    version = 1
5       u8    flags = 0 (reserved)
6       u16   glyphCount
8       u32   rangeStart
12      u32   rangeEnd
16      glyphCount × 14B index entries (ascending by cp):
          u32 cp
          i16 dwidth        (x advance, px)
          u8  bbw, u8 bbh   (bitmap width/height, px)
          i8  bbxoff, i8 bbyoff (BDF BBX offsets)
          u32 bitmapOffset  (relative to the start of the bitmap area)
after   bitmap area: bbh × ceil(bbw/8) bytes per glyph, rows top to bottom, bits MSB-first (BDF convention)
```

### C2. Variant manifest (`data/packs/<slug>/<variantId>/manifest.json`)

```json
{ "version": 1, "slug": "galmuri", "variantId": "Galmuri9",
  "pixelSize": 9, "ascent": 8, "descent": 1, "glyphCount": 12000,
  "core": { "file": "core.bin.gz", "gzBytes": 6100, "glyphs": 320 },
  "ranges": [ { "start": 0, "end": 256, "file": "00000000-00000100.bin.gz",
                "gzBytes": 1500, "glyphs": 95 } ] }
```

### C3. Python internal model (`pfc/model.py`)

```python
@dataclass
class Glyph:
    cp: int; name: str; dwidth: int
    bbw: int; bbh: int; bbx: int; bby: int
    rows: bytes                     # bbh*ceil(bbw/8), MSB-first
@dataclass
class ParsedFont:
    path: Path; family_slug: str; file_name: str
    props: dict[str, str | int]
    pixel_size: int; ascent: int; descent: int
    bbox: tuple[int, int, int, int] # (w, h, xoff, yoff)
    glyphs: list[Glyph]             # ascending by cp, only ENCODING>=0
    warnings: list[str]
```

### C4. TS decoding and rendering interfaces (`site/src/lib/`)

```ts
// glyphpack.ts
export interface DecodedGlyph { cp: number; dwidth: number; w: number; h: number;
  xoff: number; yoff: number; rows: Uint8Array }
export class GlyphChunk {
  static parse(buf: ArrayBuffer): GlyphChunk
  readonly rangeStart: number; readonly rangeEnd: number; readonly size: number
  has(cp: number): boolean
  get(cp: number): DecodedGlyph | null
}
// glyphstore.ts
export interface VariantManifest { version: 1; slug: string; variantId: string;
  pixelSize: number; ascent: number; descent: number; glyphCount: number;
  core: { file: string; gzBytes: number; glyphs: number };
  ranges: { start: number; end: number; file: string; gzBytes: number; glyphs: number }[] }
export class GlyphStore {
  constructor(dataBase: string)   // e.g. `${base}/data`
  loadManifest(slug: string, variantId: string): Promise<VariantManifest>
  glyphsFor(slug: string, variantId: string, text: string): Promise<Map<number, DecodedGlyph | null>>
}
// render.ts — pure-function rasterization into a 1:1 buffer, then wrapped and scaled up by canvas (imageSmoothing off)
export interface RenderOpts { scale: number; invert: boolean; grid: boolean;
  highlightMissing: boolean; maxWidth?: number }
export interface RasterResult { width: number; height: number;
  data: Uint8ClampedArray /* RGBA */; missing: number[] }
export function rasterize(text: string, glyphs: Map<number, DecodedGlyph | null>,
  font: { pixelSize: number; ascent: number; descent: number },
  opts: Omit<RenderOpts, "scale">): RasterResult
export function paint(canvas: HTMLCanvasElement, r: RasterResult, scale: number): void
```

Missing-glyph layout: advance = round(pixelSize/2)+1, drawing a 1px dashed box of ascent height above the baseline; when `highlightMissing` is on, fill it with the highlight color. Line breaks on `\n` only; no shaping or kerning (noted on the About page).

### C5. index.json (catalogue page; `data/index.json`)

```json
{ "generatedAt": "2026-08-21T00:00:00Z", "families": [ {
  "slug": "galmuri", "name": "Galmuri", "nameZh": "", "author": "quiple",
  "form": "gothic", "vibes": ["retro-game"], "scripts": ["ko", "latin"],
  "sizes": [7, 9, 11], "weights": ["regular"], "spacing": ["proportional"],
  "license": { "spdx": "OFL-1.1", "name": "SIL Open Font License 1.1",
               "commercial": true, "confidence": "auto-high" },
  "converted": false, "curated": true, "glyphCount": 17000,
  "hanInk": null, "inkHeight": 8,
  "badges": ["ksx1001-hangul", "kana"],
  "coverageSummary": { "gb2312": 0.02, "big5-changyong": 0.0, "jisx0208-l1": 0.31,
    "ksx1001-hangul": 1.0, "kana": 1.0, "wgl4": 0.88, "cp437": 0.75 },
  "variants": [ { "id": "Galmuri9", "file": "Galmuri9.bdf", "size": 9,
    "weight": "regular", "spacing": "proportional", "script": null,
    "glyphs": 12000 } ],
  "preview": "previews/galmuri/ko.svg", "sampleLang": "ko", "added": "2026-08-21" } ] }
```

`confidence ∈ {"auto-high","auto-low","manual","unknown"}`. `form ∈ {gothic,mingcho,rounded,kai,fangsong,serif-pixel,sans,script,decorative,terminal,other,""}` (empty = uncategorized). `scripts ⊆ {zh-hans,zh-hant,ja,ko,latin,cyrillic,greek}`.

### C6. detail.json (`data/details/<slug>.json`)

```json
{ "slug": "galmuri", "meta": { "...same as the index family entry..." : 0 },
  "homepage": "", "repository": "", "description": "", "provenance": "",
  "licenseText": "OFL.txt", "warnings": ["..."],
  "metrics": { "Galmuri9": { "pixelSize": 9, "ascent": 8, "descent": 1,
    "bbox": [9, 9, 0, -1], "hanInk": null, "capHeight": 7, "xHeight": 5,
    "maxInk": [9, 9], "maxInkCps": [65, 65], "monospaced": false,
    "dwidthHistogram": { "5": 100, "9": 11900 } } },
  "coverage": { "Galmuri9": { "gb2312-l1": [80, 3755], "hiragana": [86, 86] } },
  "unicodeBlocks": { "Galmuri9": [ ["Basic Latin", 95, 95] ] },
  "downloads": [ { "variantId": "Galmuri9", "kind": "bdf", "file": "galmuri--Galmuri9.bdf.gz",
    "bytes": 120000, "sha256": "…" } ] }
```

### C7. Coverage charset registry (`pfc/coverage/charsets.py` + `pfc/coverage/data/`)

```python
@dataclass(frozen=True)
class Charset:
    id: str; section: str          # section ∈ overview|gb|prc-lit|tw|hk|jp|kr|intl
    name_zh: str; name_en: str; desc_zh: str; desc_en: str
    cps: frozenset[int]; source: str
def load_charsets(data_dir: Path) -> list[Charset]
def coverage_for(cps: frozenset[int], charsets: list[Charset]) -> dict[str, tuple[int, int]]
def unicode_block_coverage(cps: frozenset[int], ucd: Ucd) -> list[tuple[str, int, int]]
```

Data file format (`pfc/coverage/data/<section>/<id>.txt`):

```
# id: gb2312-l1
# name_zh: GB/T 2312 一级汉字
# name_en: GB/T 2312 Level 1 Hanzi
# desc_zh: 1980 年国家标准一级常用字,按拼音排序
# desc_en: ...
# source: Python gb2312 codec, rows 16-55; generated 2026-08-21
# license: data derived from standard, factual
4E00
4E8C..4E8D
啊
```

Each line is one of three forms: `XXXX` (hex), `XXXX..YYYY` (closed interval), or literal characters (any number per line, taken character by character). `#` starts a comment.

### C8. Directory conventions and artifact paths

```
site/public/data/
  index.json
  coverage-intervals.bin.gz        # character lookup: see Task 18
  details/<slug>.json
  packs/<slug>/<variantId>/{manifest.json, core.bin.gz, XXXXXXXX-XXXXXXXX.bin.gz}
  previews/<slug>/<lang>.svg       # build-time default sample SVG
  og/<slug>.png
dist-downloads/
  manifest.json                    # [{family,variantId,kind,file,bytes,sha256}]
  galmuri--Galmuri9.bdf.gz / .pcf.gz / galmuri.zip
```

`variantId` = the filename with its extension stripped, restricted to `[A-Za-z0-9_-]` (everything else replaced with `-`). `slug` = the family directory name.

---

## Phase A — Pipeline Core

### Task 1: Repository scaffolding

**Files:**
- Create: `.gitignore`, `Makefile`, `README.md`
- Create: `pipeline/pyproject.toml`, `pipeline/opf/__init__.py` (`PIPELINE_VERSION = 1`), `pipeline/tests/test_smoke.py`
- Create: `site/package.json`, `site/astro.config.mjs`, `site/tsconfig.json`, `site/svelte.config.js`, `site/vitest.config.ts`, `site/src/lib/version.ts`, `site/src/lib/version.test.ts`, `site/src/pages/index.astro` (temporary placeholder)

**Interfaces:**
- Produces: `make py-test` (pipeline pytest), `make ts-test` (site vitest), `make dev`, `make build`; Python venv `.venv`; `import opf` works.

- [x] **Step 1: Python-side scaffolding + smoke test**

`pipeline/pyproject.toml`:

```toml
[project]
name = "open-pixel-fonts"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fonttools>=4.60", "freetype-py>=2.5", "Pillow>=10"]
[project.optional-dependencies]
dev = ["pytest>=8"]
[tool.pytest.ini_options]
testpaths = ["tests"]
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
[tool.setuptools.packages.find]
include = ["opf*"]
```

`pipeline/tests/test_smoke.py`:

```python
import opf
def test_pipeline_version():
    assert opf.PIPELINE_VERSION == 1
```

- [x] **Step 2: create the venv and verify pytest passes**

```bash
python3 -m venv .venv && .venv/bin/pip -q install -e "pipeline[dev]"
.venv/bin/pytest pipeline/tests -q   # expect 1 passed
```

- [x] **Step 3: site scaffolding (Astro5 + Svelte5 + TS strict + vitest) + smoke test**

`site/src/lib/version.ts` exports `export const SITE_VERSION = 1`; `version.test.ts` asserts it. `npm create astro` cannot be used interactively, so write a minimal `package.json` by hand (deps: astro@^5, @astrojs/svelte@^7, svelte@^5; dev: typescript, vitest, with playwright added later in Task 15) plus `astro.config.mjs` (svelte integration, `base: process.env.OPF_BASE ?? '/open-pixel-fonts'`).

- [x] **Step 4: verify `npm install && npx vitest run` passes and `npx astro build` succeeds**

- [x] **Step 5: Makefile (fonts/dev/build/py-test/ts-test/test targets) and .gitignore (`.venv/ node_modules/ dist/ .cache/ site/public/data/ dist-downloads/ __pycache__/`), then commit**

```bash
git add -A && git commit -m "chore: repository scaffolding (pfc package + Astro/Svelte site)"
```

### Task 2: BDF parser

**Files:**
- Create: `pipeline/opf/model.py` (contract C3), `pipeline/opf/parsers/__init__.py`, `pipeline/opf/parsers/bdf.py`
- Create: `pipeline/tests/fixtures/mini.bdf` (hand-built, 3 glyphs: A, the Han character 永, and a combining mark), `pipeline/tests/test_bdf.py`

**Interfaces:**
- Produces: `parse_bdf(path: Path, family_slug: str) -> ParsedFont`; `.bdf.gz` is transparently decompressed; non-fatal issues go into `ParsedFont.warnings`.

- [x] **Step 1: write the fixture and the failing test**

`mini.bdf` contents (written out in full, including `SIZE 16 75 75`, `FONTBOUNDINGBOX 16 16 0 -2`, `PIXEL_SIZE 16`, `FONT_ASCENT 14`, `FONT_DESCENT 2`, and the glyphs `A` (ENCODING 65, DWIDTH 8 0, BBX 7 10 0 0), `uni6C38` (ENCODING 27704, DWIDTH 16 0, BBX 16 15 0 -1), and one ENCODING -1 glyph that should be skipped).

Core assertions in `test_bdf.py`:

```python
from pathlib import Path
from opf.parsers.bdf import parse_bdf
FIX = Path(__file__).parent / "fixtures"

def test_parse_mini_bdf():
    f = parse_bdf(FIX / "mini.bdf", "mini")
    assert f.pixel_size == 16 and f.ascent == 14 and f.descent == 2
    assert f.bbox == (16, 16, 0, -2)
    assert [g.cp for g in f.glyphs] == [65, 27704]      # -1 skipped, ascending
    a = f.glyphs[0]
    assert (a.dwidth, a.bbw, a.bbh, a.bbx, a.bby) == (8, 7, 10, 0, 0)
    assert len(a.rows) == 10 * 1                         # ceil(7/8)=1
    assert f.props["FOUNDRY"] == "test"

def test_parse_gz(tmp_path):
    import gzip, shutil
    gz = tmp_path / "mini.bdf.gz"
    with open(FIX / "mini.bdf", "rb") as s, gzip.open(gz, "wb") as d:
        shutil.copyfileobj(s, d)
    assert len(parse_bdf(gz, "mini").glyphs) == 2

def test_bad_bitmap_line_warns():
    f = parse_bdf(FIX / "mini-bad.bdf", "mini")          # BITMAP line length mismatch
    assert any("bitmap" in w.lower() for w in f.warnings)
```

- [x] **Step 2: run and confirm it fails (module does not exist)**: `.venv/bin/pytest pipeline/tests/test_bdf.py -q`

- [x] **Step 3: implement `bdf.py`**

Key points: a line-by-line state machine (header → properties → chars); `ENCODING` is read as decimal, with negative values skipped but counted; hexadecimal `BITMAP` lines are truncated/zero-padded to `ceil(bbw/8)` bytes with a warning; a duplicate ENCODING keeps the first and records a warning; `SIZE` pt@dpi → px = round(pt × dpi/72) only when `PIXEL_SIZE` is absent; when `FONT_ASCENT/DESCENT` are missing, derive them from `FONTBOUNDINGBOX` (ascent = h+yoff… ascent = bbox_h + bbox_yoff, descent = -bbox_yoff) and record a warning; the `open` branch: use `gzip.open` for the `.gz` suffix; read as latin-1 (BDF properties may contain non-ASCII).

- [x] **Step 4: once the tests pass, add integration assertions against a real font from the collection folder (copied in as a fixture)**

```bash
cp "/home/chen/githubprojects/pixelfontworkshop/pixel-font-collection-fonts/CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/quiple--galmuri/dist/Galmuri7.bdf" pipeline/tests/fixtures/real-galmuri7.bdf
```

Additional assertions: glyph count > 1000, every `len(rows) == bbh*ceil(bbw/8)`, cp strictly increasing.

- [x] **Step 5: everything passes, commit** `feat: BDF parser`

### Task 3: Size and ink metrics

**Files:**
- Create: `pipeline/opf/metrics.py`, `pipeline/tests/test_metrics.py`

**Interfaces:**
- Consumes: `ParsedFont`, `Glyph`
- Produces:

```python
@dataclass
class InkMetrics:
    han_ink: tuple[int, int] | None
    cap_height: int | None
    x_height: int | None
    max_ink: tuple[int, int]
    max_ink_cps: tuple[int, int]
def glyph_ink_size(g: Glyph) -> tuple[int, int] | None   # lit-pixel bounding box (w,h); empty = None
def compute_ink(f: ParsedFont, han_ref: frozenset[int]) -> InkMetrics
def is_monospaced(f: ParsedFont) -> bool                 # ≥99% of glyphs share one dwidth
def claimed_size(f: ParsedFont) -> int
```

- [x] **Step 1: failing tests** (constructing `Glyph` objects and testing them directly)

```python
def _g(cp, w, h, bits):  # bits: list[str] e.g. ["0100000","1110000"]
    rows = bytes(int(r.ljust((len(r)+7)//8*8, "0"), 2).to_bytes((len(r)+7)//8, "big")[i]
                 for r in bits for i in range((len(r)+7)//8))
    return Glyph(cp=cp, name=f"u{cp:x}", dwidth=w, bbw=w, bbh=h, bbx=0, bby=0, rows=rows)

def test_ink_bbox_trims_margins():
    g = _g(0x4E00, 8, 8, ["00000000","00111100","00100100","00111100",
                          "00000000","00000000","00000000","00000000"])
    assert glyph_ink_size(g) == (4, 3)

def test_empty_glyph_none():
    assert glyph_ink_size(_g(32, 8, 8, ["00000000"]*8)) is None

def test_han_ink_median():  # three Han glyphs with ink (14,14),(15,15),(16,16) → median (15,15)
    ...
def test_monospace_tolerance():  # 100 glyphs, 99 with dwidth=8 and 1 with 4 → True; 95/5 → False
    ...
```

(`test_han_ink_median` / `test_monospace_tolerance` are written out in full using `_g` as above.)

- [x] **Step 2: run and confirm failure** → **Step 3: implement** (median via `statistics.median_low`; when the han_ref intersection is < 100, fall back to all U+4E00–9FFF ∪ extension block glyphs; cap = median ink height of A–Z, x = median ink height of "acemnorsuvwxz" among a–z) → **Step 4: passing** → **Step 5: commit** `feat: claimed/ink metrics`

### Task 4: Charset data foundation (codec-derived + legacy data migration + UCD)

**Files:**
- Create: `pipeline/opf/coverage/__init__.py`, `charsets.py` (contract C7), `ucd.py`
- Create: `pipeline/opf/coverage/gen/gen_codec_tables.py` (generator; the generated output is committed)
- Create: `pipeline/opf/coverage/data/…` (generated/migrated .txt), `pipeline/opf/coverage/data/ucd/` (Blocks.txt + assigned-ranges.txt)
- Create: `pipeline/tests/test_charsets.py`, `THIRD_PARTY_NOTICES.md`
- Migrate: `cp ../open-pixel-fonts-old/scripts/data/cjk-tables/*.txt` → convert into C7 format under `data/` (gb12345, tongyong-guifan (the whole table), 7000tongyong, 3500changyong, yiwu-jiaoyu, guji, iicore, hanyi, fangzheng, 4808, 6343, big5changyong, big5, hkchangyong, hkscs, suppchara)

**Interfaces:**
- Produces: `load_charsets(data_dir) -> list[Charset]`; `Ucd` (`blocks: list[tuple[str,int,int]]`, `assigned: frozenset[int]`, `block_assigned_counts`); the generator is rerunnable and idempotent.

- [x] **Step 1: failing tests — assertions on known constants**

```python
def test_known_counts():
    cs = {c.id: c for c in load_charsets(DATA)}
    assert len(cs["gb2312-l1"].cps) == 3755
    assert len(cs["gb2312-l2"].cps) == 3008
    assert len(cs["big5-changyong"].cps) == 5401
    assert len(cs["ksx1001-hangul"].cps) == 2350
    assert len(cs["ksx1001-hanja"].cps) == 4888          # 4620 after deduplicating repeated hanja by code point; assert the actual generated value and document it
    assert len(cs["jisx0208-l1"].cps) == 2965
    assert len(cs["jisx0208-l2"].cps) == 3390
    assert len(cs["hiragana"].cps) == 86                  # U+3041..3096 + 309D..309F per the definition file
    assert len(cs["kangxi-radicals"].cps) == 214
    assert len(cs["cp437"].cps) == 256
def test_loader_formats(tmp_path):
    # write a temporary table containing hex, interval, and literal lines, and assert the parsed union is correct
    ...
def test_every_table_has_metadata():
    for c in load_charsets(DATA):
        assert c.name_zh and c.name_en and c.source
def test_ucd_blocks():
    u = load_ucd(DATA / "ucd")
    assert ("Basic Latin", 0x0000, 0x007F) in u.blocks
    assert u.block_assigned_counts["Basic Latin"] == 128
```

Note: if running the generator conflicts with the constant assertions (e.g. ksx1001-hanja deduplication), correct the assertion against the authoritative source, document the counting rule in the data file header, and then commit.

- [x] **Step 2: confirm failure** → **Step 3: implement the loader and the generator**

Generator key points: GB2312 Levels 1 and 2 by row/cell (rows 16–55 / 56–87) via `bytes([0xA0+r, 0xA0+c]).decode('gb2312')`; Big5 frequently used A440–C67E and less frequently used C940–F9D5 via the `big5` codec; JIS X 0208 levels by row (rows 1–8 non-kanji, 16–47 Level 1, 48–84 Level 2) via `euc_jp`; JIS X 0213 Levels 3 and 4 via `euc_jis_2004` (enumerating plane/row/cell; Level 3 = the rows added in plane 1, Level 4 = plane 2); KS X 1001 Hangul rows 16–40 and hanja rows 42–93 via `euc_kr`; GBK Han characters and all GB18030 Han characters enumerated via the `gb18030` codec. Kana / Bopomofo / radicals / Braille / box drawing / block elements / Powerline (U+E0A0–E0A2, U+E0B0–E0B3 basic + U+E0A3, U+E0B4–E0D4 extended) / halfwidth kana / JIS X 0201 / Hangul syllables and Jamo: written into data files directly as ranges. UCD: download the Unicode 17.0 `Blocks.txt` + `UnicodeData.txt` to generate `assigned-ranges.txt` (falling back to Python's `unicodedata` when the network is unavailable, noting the version in the source field). The legacy data migration script converts the format in one pass and preserves the CJK-character-count MIT notice in `THIRD_PARTY_NOTICES.md`.

- [x] **Step 4: passing** → **Step 5: commit** `feat: charset data foundation and UCD (codec-derived + migrated)`

### Task 5: External charset acquisition (online research, artifacts committed offline)

**Files:**
- Create: `pipeline/opf/coverage/data/jp/joyo-2136.txt`, `jp/kyoiku-1026.txt`, `jp/jinmeiyo.txt`, `gb/gb18030-2022-l1.txt`, `-l2.txt`, `-l3.txt`, `intl/unihan-core-2020.txt`, `intl/wgl4.txt`, `intl/viet-latin.txt`, `prc-lit/tongyong-guifan-l1/-l2/-l3.txt`, `prc-lit/changyong-2500.txt`, `prc-lit/cichangyong-1000.txt`
- Modify: `pipeline/tests/test_charsets.py` (add count assertions), `THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Produces: the tables above appear in the `load_charsets` result; each table's header cites an authoritative source.

- [x] **Step 1: add failing assertions** (joyo=2136, kyoiku=1026, tongyong-guifan l1+l2+l3=8105, changyong-2500 + cichangyong-1000=3500, wgl4=652; the GB18030-2022 level counts are taken from the standard text and filled in after research)
- [x] **Step 2: research an authoritative source for each table online (the standard text / official gazettes / the Unicode Unihan kUnihanCore2020 and kIICore fields) → generate the data files (parallel subagents may be dispatched to fetch data separately, with the results verified centrally in this task)**
- [x] **Step 3: assertions pass; sources written into the file headers and into THIRD_PARTY_NOTICES**
- [x] **Step 4: commit** `feat: standard and international character set data`

### Task 6: Coverage engine

**Files:**
- Create: `pipeline/opf/coverage/engine.py`, `pipeline/tests/test_coverage.py`

**Interfaces:**
- Consumes: `Charset`, `Ucd`, `ParsedFont`
- Produces:

```python
def font_cps(f: ParsedFont) -> frozenset[int]
def coverage_for(cps, charsets) -> dict[str, tuple[int, int]]
def unicode_block_coverage(cps, ucd) -> list[tuple[str, int, int]]   # only blocks with have>0, plus a "full table mode" parameter
def overview(cps, ucd) -> dict   # total/planes/pua3/han_total/compat (including the data for the 12-character footnote)
def badges(cov: dict[str, tuple[int,int]]) -> list[str]              # thresholds: see the badge rules in spec §7
def detect_scripts(cov) -> list[str]                                  # thresholds: gb2312-l1≥50%→zh-hans; big5-changyong≥50%→zh-hant; hiragana&katakana≥90%→ja; ksx1001-hangul≥50%→ko; latin-basic≥90%→latin
```

- [x] **Step 1: failing tests** (synthetic cps sets: all of GB2312 Level 1 → `coverage_for` returns (3755,3755) for that table and badges include `gb2312`… one case per branch, covering the 12-character compatibility footnote and the three PUA areas)
- [x] **Step 2: confirm failure** → **Step 3: implement** → **Step 4: passing** → **Step 5: commit** `feat: coverage engine`

### Task 7: License detection

**Files:**
- Create: `pipeline/opf/licenses.py`, `pipeline/opf/licenses_data/` (canonical text fragments of known licenses), `pipeline/tests/test_licenses.py`, `pipeline/tests/fixtures/licenses/` (real texts copied from the collection folder: OFL.txt, MIT, Apache, IPA, M+, Baekmuk, etc.)

**Interfaces:**
- Produces:

```python
@dataclass
class LicenseInfo:
    spdx: str | None; name: str; file: str | None
    commercial: bool | None; confidence: str  # auto-high|auto-low|manual|unknown
    note: str = ""
def detect_license(family_dir: Path, fonts: list[ParsedFont],
                   toml_override: dict | None) -> LicenseInfo
COMMERCIAL_OK = {"OFL-1.1","OFL-1.0","MIT","Apache-2.0","CC0-1.0","Unlicense",
                 "WTFPL","CC-BY-4.0","CC-BY-SA-4.0","IPA-1.0","GPL-2.0-with-font-exception",
                 "GPL-3.0-with-font-exception","LicenseRef-Mplus","LicenseRef-Baekmuk"}
```

- [x] **Step 1: failing tests**: each real text → the expected spdx with `auto-high`; only a BDF `COPYRIGHT` hint → `auto-low`; a toml override wins over everything → `manual`; nothing at all → `unknown`. Detection method: normalize (lowercase, collapse whitespace, strip copyright lines) and then match against **characteristic phrase groups** (e.g. OFL-1.1 must contain both "sil open font license" and "version 1.1"; GPL+FE must contain "font exception"); a whole-text hash cannot be used (the copyright line varies).
- [x] **Step 2–5: fail → implement → pass → commit** `feat: license detection (fingerprints + three confidence levels)`

### Task 8: family.toml and variant resolution

**Files:**
- Create: `pipeline/opf/familymeta.py`, `pipeline/tests/test_familymeta.py`

**Interfaces:**
- Consumes: `ParsedFont`, `LicenseInfo`
- Produces:

```python
@dataclass
class VariantDesc:
    id: str; file: str; size: int; weight: str; spacing: str
    script_subset: str | None; display: str
@dataclass
class FamilyMeta:  # the complete view after parsing the toml and deriving defaults
    slug: str; name: str; name_zh: str; author: str; homepage: str
    repository: str; description: str; form: str; vibes: list[str]
    converted_from: str; provenance: str; curated: bool
    license_override: dict | None; samples: dict[str, str]
    variant_overrides: dict[str, dict]
def load_family_meta(family_dir: Path) -> FamilyMeta        # no toml → write a stub to disk + curated=False
def resolve_variant(f: ParsedFont, meta: FamilyMeta) -> VariantDesc
```

- [x] **Step 1: failing tests**: full toml parsing; with no toml, a stub is generated (contents include TODO comments, name = the directory name title-cased) and `curated=False`; variant derivation: `WEIGHT_NAME=Bold`→bold, a filename containing `-bold`→bold, `SPACING∈{C,M}`→monospaced, a filename with `zh_hans`→`zh-hans`; `[variants]` overrides win over everything; illegal characters in `variantId` are replaced.
- [x] **Step 2–5: fail → implement (read with `tomllib`, write the stub from a string template) → pass → commit** `feat: family.toml and variant resolution`

### Task 9: Glyph pack writer

**Files:**
- Create: `pipeline/opf/glyphpack.py`, `pipeline/tests/test_glyphpack.py`

**Interfaces:**
- Consumes: `ParsedFont`, `VariantDesc`; contracts C1/C2/C8
- Produces:

```python
CORE_TEXT: str  # printable ASCII + hiragana/katakana + Hangul Compatibility Jamo + every character used in the default sample sentences (spec §5.2)
def plan_chunks(cps: list[int]) -> list[tuple[int, int]]   # aligned to 256-blocks; split on a gap > 16 blocks; split when the raw estimate exceeds 48KB
def write_packs(f: ParsedFont, v: VariantDesc, meta_name: str, out_dir: Path) -> dict  # returns the manifest dict and writes to disk
def read_chunk(path: Path) -> list[Glyph]                  # read back on the Python side, for tests and cross-language fixtures
```

- [x] **Step 1: failing tests**: mini font → manifest ranges correct; `read_chunk(write(…))` round-trips field for field; byte-level golden assertion (the first 16 bytes of the mini font's chunk == `b"PFG1\x01\x00\x02\x00..."`); determinism (two writes produce the same sha256, gzip mtime=0); the core pack contains the family-name characters; the real galmuri fixture: every chunk ≤ 16KB gz (exemptions may be listed: a single fully populated 256-cp block from a 32×64 font is bounded by the 48KB raw split ceiling).
- [x] **Step 2–5: fail → implement (`struct.pack("<IHH…")` style; greedy chunk merging) → pass → commit** `feat: glyph pack v1 writer`

### Task 10: TS glyph pack decoder

**Files:**
- Create: `site/src/lib/glyphpack.ts`, `site/src/lib/glyphpack.test.ts`, `site/src/lib/decompress.ts`
- Create: `site/src/lib/__fixtures__/mini-chunk.bin` (generated in the tests by the Python writer from Task 9, then copied in and committed)

**Interfaces:**
- Consumes: the C1 binary; Produces: the C4 `GlyphChunk`. `decompress.ts`: `gunzip(buf: ArrayBuffer): Promise<ArrayBuffer>` using `DecompressionStream`, with a `node:zlib` branch for the Node test environment.

- [x] **Step 1: failing test**

```ts
import { readFileSync } from "node:fs";
import { GlyphChunk } from "./glyphpack";
const buf = readFileSync(new URL("./__fixtures__/mini-chunk.bin", import.meta.url));
test("parses python-written chunk", () => {
  const c = GlyphChunk.parse(buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength));
  expect(c.size).toBe(2);
  const a = c.get(65)!;
  expect([a.dwidth, a.w, a.h, a.xoff, a.yoff]).toEqual([8, 7, 10, 0, 0]);
  expect(a.rows.length).toBe(10);
  expect(c.get(66)).toBeNull();
  expect(c.has(27704)).toBe(true);
});
```

- [x] **Step 2–5: fail → implement (DataView + binary search) → pass → commit** `feat: TS glyph pack decoder (cross-language contract tests)`

### Task 11: Pure-function rasterization and canvas painting

**Files:**
- Create: `site/src/lib/render.ts`, `site/src/lib/render.test.ts`

**Interfaces:** contract C4 (`rasterize`/`paint`/`RenderOpts`/`RasterResult`).

- [x] **Step 1: failing tests**: a single glyph A (using the Task 10 fixture) → output size = (dwidth, ascent+descent); the pixel at bit (x,y) is black; inverted after `invert`; a missing character returns `missing:[cp]` with a placeholder box of width round(16/2)+1; `\n` breaks the line; `maxWidth` breaks within a word; the grid option draws gridlines at scale ≥ 4 (rasterize does not handle grid — grid belongs to the paint layer, so the test only checks that rasterize's data is correct).
- [x] **Step 2–5: fail → implement (rasterize is pure TS emitting RGBA; paint uses `putImageData` onto an offscreen 1:1 canvas and then `drawImage` to scale up, with `imageSmoothingEnabled=false`) → pass → commit** `feat: pixel rasterization and painting`

### Task 12: SVG prerendering and og images

**Files:**
- Create: `pipeline/opf/prerender.py`, `pipeline/tests/test_prerender.py`

**Interfaces:**
- Consumes: `ParsedFont`, the sample sentence constant `SAMPLES: dict[str, str]` (the default sentences from spec §5.2, defined in this module and referenced by `glyphpack.CORE_TEXT`)
- Produces: `sample_svg(f, text, fg="#1a1a1a") -> str` (horizontal runs merged into rects, viewBox at 1:1 pixels, `shape-rendering="crispEdges"`); `og_png(f, name, text, out: Path)` (1200×630, Pillow, nearest-neighbor pixel upscaling).

- [x] **Step 1: failing tests**: mini font with "A" → the SVG rect count == the number of horizontal runs in A; viewBox width == dwidth; a missing character produces a placeholder rect (with `class="missing"`); the og output PNG is 1200×630.
- [x] **Step 2–5: fail → implement → pass → commit** `feat: SVG prerendering and og cards`

### Task 13: Downloadables build

**Files:**
- Create: `pipeline/opf/downloads.py`, `pipeline/tests/test_downloads.py`

**Interfaces:**
- Produces: `build_downloads(families: list[BuiltFamily], out: Path) -> dict` (the manifest; `BuiltFamily` is defined in Task 14). Artifacts follow C8: `<slug>--<variantId>.bdf.gz`, `.pcf.gz` (a `bdftopcf` subprocess; on failure record a warning and emit only the BDF), `<slug>.zip` (the original BDFs + license + a README.txt containing the provenance). gzip/zip timestamps are pinned (1980-01-01) to guarantee determinism.

- [x] **Step 1: failing tests** (mini family → all three artifact kinds exist, sha256 matches the manifest, the zip contains LICENSE and README.txt, a rerun produces identical bytes; skip the pcf assertions when `shutil.which("bdftopcf")` is missing)
- [x] **Step 2–5: fail → implement → pass → commit** `feat: BDF/PCF/zip download artifacts and manifest`

### Task 14: Build orchestrator and index emission

**Files:**
- Create: `pipeline/opf/build.py` (entry point `python -m opf.build`), `pipeline/opf/emit.py`, `pipeline/opf/cache.py`, `pipeline/tests/test_build.py`
- Create: `pipeline/tests/fixtures/fonts-tree/` (two families: mini plus the real galmuri files, including one family with no toml)
- Create: `site/src/lib/schema.ts` (zod) and `site/src/lib/schema.test.ts`

**Interfaces:**
- Consumes: everything from Tasks 2–13
- Produces:

```python
@dataclass
class BuiltVariant:
    desc: VariantDesc; font: ParsedFont; ink: InkMetrics
    coverage: dict[str, tuple[int, int]]; blocks: list; overview: dict
@dataclass
class BuiltFamily:
    meta: FamilyMeta; license: LicenseInfo; variants: list[BuiltVariant]
def build(fonts_dir: Path, site_data: Path, downloads: Path, cache_dir: Path) -> BuildReport
```

CLI: `--fonts fonts/ --out site/public/data --downloads dist-downloads --cache .cache [--family <slug>]`. emit writes output per C5/C6/C8; `badges`/`scripts`/`sampleLang` use the Task 6 functions; caching is family-level, keyed on the sha256 of every source file + PIPELINE_VERSION, and a hit skips recomputation (the artifacts are already on disk). Size red line: at the end, total up `site/public/data`; exit code 2 if it exceeds 900MB.

- [x] **Step 1: failing tests**: a full build of the fixtures tree → index.json has 2 families, the toml-less family has `curated:false` with the stub written, details/packs/previews/og/downloads are all present, a second build hits the cache (mtime unchanged and the log contains "cached"), and `--family` rebuilds only that one family.
- [x] **Step 2: zod schema test**: `schema.ts` defines zod models for C5/C6; vitest reads the fixture index.json produced by pytest (a copy is committed to `site/src/lib/__fixtures__/index.fixture.json`) and validates it — a cross-language contract.
- [x] **Step 3–5: fail → implement → pass → commit** `feat: build orchestrator, index emission, and incremental cache`

## Phase B — Site

### Task 15: Astro skeleton, i18n, theme foundation

**Files:**
- Create: `site/src/i18n/{types.ts,zh.ts,en.ts,index.ts}` (`t(lang)` looks up strings; `en.ts` is produced by an Opus/Sonnet subagent translation)
- Create: `site/src/layouts/Base.astro` (html lang, hreflang alternate, theme switch script, header/footer, design token CSS)
- Create: `site/src/styles/tokens.css` (paper-white / charcoal dual theme variables, cinnabar red accent, spacing and type scales)
- Create: `site/src/pages/index.astro` (language redirect page), `site/src/pages/[lang]/index.astro` (catalogue page shell), `site/src/pages/[lang]/about.astro`, `site/src/pages/404.astro`
- Create: `site/src/lib/data.ts` (`loadIndex()` reads `site/public/data/index.json` from the filesystem at build time; `withBase(path)`)
- Create: `site/e2e/smoke.spec.ts`, `site/playwright.config.ts`; Modify: `site/package.json` (add playwright)

**Interfaces:**
- Consumes: the Task 14 artifacts (built from fixture data)
- Produces: the `UIStrings` interface and `t()`; the `Base.astro` slot layout; `withBase`; the e2e foundation (`npx playwright test`, with webServer starting `astro preview`).

- [x] **Step 1: run the pipeline over the fixtures to generate `site/public/data/`**: `.venv/bin/python -m opf.build --fonts pipeline/tests/fixtures/fonts-tree --out site/public/data --downloads dist-downloads --cache .cache`
- [x] **Step 2: failing e2e**: `/zh/` returns 200 and contains the site name 开源像素字体馆, html[lang=zh], and an hreflang en link; `/en/` shows the English site name; `/` contains the redirect script; toggling dark mode writes localStorage and changes html[data-theme].
- [x] **Step 3: implement the skeleton and style foundation (tokens: `--bg` paper white / `--ink` charcoal / `--accent` cinnabar red #c3272b family, inverted in dark mode; component classes for the progress-bar squares and the 1px rules)**
- [x] **Step 4: dispatch an Opus/Sonnet subagent to translate `zh.ts` → `en.ts` (including review); integration happens within this task**
- [x] **Step 5: e2e passes; commit** `feat: site skeleton, bilingual routing, and theme foundation`

### Task 16: Catalogue page (filters, cards, global sample)

**Files:**
- Create: `site/src/lib/filters.ts`, `site/src/lib/filters.test.ts`, `site/src/lib/urlstate.ts`, `site/src/lib/urlstate.test.ts`, `site/src/lib/glyphstore.ts`, `site/src/lib/glyphstore.test.ts`
- Create: `site/src/islands/Catalogue.svelte`, `site/src/islands/FontCard.svelte`, `site/src/islands/FilterPanel.svelte`
- Modify: `site/src/pages/[lang]/index.astro` (mount `<Catalogue client:load>`; SSR emits the first 24 cards as static HTML using the preview SVGs)
- Create: `site/e2e/catalogue.spec.ts`

**Interfaces:**
- Consumes: C4/C5, `t()`, `withBase`
- Produces:

```ts
export interface FilterState { q: string; forms: string[]; vibes: string[];
  sizes: number[]; inkH: [number, number] | null; scripts: string[];
  licenses: string[]; commercialOnly: boolean; spacing: string[]; weights: string[];
  origin: "all" | "native" | "converted"; coverage: { id: string; min: number }[];
  chars: string; sort: "name" | "size" | "glyphs" | "added" }
export function applyFilters(fams: FamilyIndex[], s: FilterState,
  charLookup?: (slug: string, chars: string) => boolean): FamilyIndex[]
export function encodeState(s: FilterState): URLSearchParams
export function decodeState(p: URLSearchParams): FilterState
```

`GlyphStore` follows C4 (chunk LRU=64, in-flight deduplication).

- [x] **Step 1: failing tests for filters/urlstate** (one case per filter dimension + combinations + encode/decode round-trip identity + unknown parameters ignored)
- [x] **Step 2: implement the pure functions, vitest passes**
- [x] **Step 3: failing tests for glyphstore** (mock fetch and count: concurrent requests for the same chunk fetch only once; LRU eviction; `glyphsFor` covers gaps left by the core pack) → implement until passing
- [x] **Step 4: implement the Svelte islands**: FilterPanel (chips/ranges/search, bilingual), FontCard (name canvas + sample canvas, IntersectionObserver lazy rendering, badges/chips), Catalogue (state ↔ URL, sorting, simple windowing above 60 families: render only the viewport ±2 screens). The global sample input is debounced by 150ms.
- [x] **Step 5: e2e**: the card count changes after filtering on form=gothic; a card's canvas `toDataURL` differs before and after typing sample text; ×2 zoom doubles the size; opening a URL with `?forms=gothic` restores that state; toggling invert changes the background.
- [x] **Step 6: commit** `feat: catalogue page filters and editable sample cards`

### Task 17: Family detail page (sample editor, ink diagram, metadata)

**Files:**
- Create: `site/src/pages/[lang]/fonts/[slug].astro` (getStaticPaths iterates the index; SSR static output: header, metadata sidebar, prerendered SVG sample, download area, ink diagram SVG)
- Create: `site/src/islands/SampleEditor.svelte`, `site/src/components/InkDiagram.astro`, `site/src/components/MetaSidebar.astro`, `site/src/components/DownloadList.astro`
- Create: `site/e2e/detail.spec.ts`

**Interfaces:**
- Consumes: C4/C6, GlyphStore, rasterize/paint, `t()`
- Produces: the variant switch event `variantchange` (CustomEvent<string>, listened to by each island on the detail page); `InkDiagram` props `{bbox, hanInk, claimed}`.

- [x] **Step 1: failing e2e**: the galmuri fixture detail page contains the author, the license badge (auto-high copy), and a BDF download link per variant (href containing the `dist-downloads` dev base) with its byte count; typing あ into the sample text box changes the canvas and updates the missing-character count badge; switching variants changes the numbers in the metrics table; the full license text `<details>` expands and is visible.
- [x] **Step 2: implement the static parts (including the ink diagram: a three-layer SVG overlay of the claimed box, the Han ink box, and the max-ink dashed box, plus a legend)**
- [x] **Step 3: implement SampleEditor (multi-line, preset sentence buttons, zoom, invert, grid, missing-glyph highlight toggle; show a retry bar when a fetch fails)**
- [x] **Step 4: e2e passes** → **Step 5: commit** `feat: family detail page and sample editor`

### Task 18: Coverage report UI, glyph grid, character lookup

**Files:**
- Create: `site/src/islands/CoverageReport.svelte` (collapsible sections, pixel-square progress bars, variant switching, expandable missing-character list for rows with ≤500 missing, collapsible full Unicode block table)
- Create: `site/src/islands/GlyphGrid.svelte` (block jump navigation, virtual scrolling, click-to-inspect overlay: magnified bitmap canvas + code point/name/metrics)
- Create: `site/src/lib/intervals.ts` + `intervals.test.ts` (character lookup data; format = gzipped `u32 familyCount, per family: u16 slugLen + utf8, u32 runCount, runCount×(u32 start, u32 end)`; `export class CoverageIndex { static parse(buf): CoverageIndex; covers(slug, text): boolean }`)
- Modify: `pipeline/opf/emit.py` (emit `coverage-intervals.bin.gz`) + add assertions to `pipeline/tests/test_build.py`
- Modify: `site/src/islands/Catalogue.svelte` (wire in the chars filter, lazily loading CoverageIndex)
- Create: `site/e2e/coverage.spec.ts`

**Interfaces:**
- Consumes: C6 coverage/unicodeBlocks, C5 variants, GlyphStore
- Produces: `CoverageIndex` (injected into filters.ts as `charLookup`).

- [x] **Step 1: failing tests on both sides of intervals** (Python writes → TS parses; `covers("mini","永")===true`, `covers("mini","龘")===false`) → implement until passing
- [x] **Step 2: failing e2e**: the detail page's GB/T 2312 row shows n/3755 and a percentage; the numbers change when switching variants; a row with ≤500 missing characters expands and its first missing character is correct; scrolling the glyph grid to the CJK block renders glyphs, and clicking one opens the inspector; typing 永 into the catalogue page's character lookup keeps the mini family and removes families lacking that character.
- [x] **Step 3: implement the three islands and wire them up** → **Step 4: e2e passes** → **Step 5: commit** `feat: coverage report, glyph grid, and character lookup`

### Task 19: About page, 404, complete metadata

**Files:**
- Modify: `site/src/pages/[lang]/about.astro` (Chinese body copy: inclusion criteria / metric definitions / coverage methodology — rewritten from spec §4.2/§4.3 into reader-facing prose, the no-shaping note, the charset source acknowledgement table (generated automatically by iterating charset metadata), a contribution guide with a full-field family.toml example, and the license disclaimer; the English version is translated by a subagent)
- Modify: `site/src/pages/404.astro` (a 404 rendered as SVG in a collection font)
- Modify: `site/src/layouts/Base.astro` (per-page og:image/description/canonical)
- Create: `site/e2e/about.spec.ts`

- [x] **Step 1: failing e2e** (about contains the word "ink" and an acknowledgement table with at least as many rows as there are charsets; the detail page's og:image points at `data/og/<slug>.png`; the 404 contains a pixel rendering)
- [x] **Step 2: write the Chinese body copy → subagent translation → integrate** → **Step 3: e2e passes** → **Step 4: commit** `feat: about page and metadata`

## Phase C — Import and Full Corpus

### Task 20: Import tooling (zip/BDF/OTB/kbitx) and the five pilot families

**Files:**
- Create: `pipeline/opf/ingest/__init__.py`, `manifest.py` (reads `ingest/manifest.toml`), `extract.py` (unpack a zip and take the BDFs), `otb.py` (fonttools EBDT/EBLC → Glyph → write BDF), `kbitx.py` (XML → BDF), `bdfwrite.py` (`write_bdf(f: ParsedFont, out: Path)`), `run.py` (CLI `python -m opf.ingest.run --manifest … --src … --dest fonts/ [--only slug]`)
- Create: `pipeline/tests/test_ingest.py` (real files: one galmuri zip, a wqy otb, one kbitx)
- Create: `ingest/manifest.toml` (pilot entries only at first) + `docs/import-report.md` (tool-generated)

**Interfaces:**
- Produces: the manifest entry schema:

```toml
[[family]]
slug = "baekmuk-batang"
source = "CJK-bitmap-fonts-open-source-2026-08-18/Korean/chocolatemelt--baekmuk"
take = ["batang*.bdf"]            # glob; or zip = "RELEASE-ASSETS/x.zip", zip_take=["*.bdf"]
license_files = ["COPYRIGHT*"]
name = "Baekmuk Batang"
provenance_url = "https://github.com/chocolatemelt/baekmuk"
convert = ""                       # ""|"otb"|"kbitx"|"ttf"
```

Idempotence: target exists with the same content sha → skip; the report records imported/skipped/deduped/todo.

- [x] **Step 1: failing unit tests** (zip extraction and renaming; otb→BDF then `parse_bdf` round-trips to the same glyph count; kbitx→BDF likewise; `write_bdf` and `parse_bdf` round-trip identically; an idempotent rerun skips)
- [x] **Step 2: implement the four paths and the report** → **Step 3: unit tests pass**
- [x] **Step 4: pilot-import 5 families**: ark-pixel (3 sizes, zip), galmuri (zip), batang from the four-way baekmuk split, UnifontEX (a single 12MB BDF as a stress test), and wqy-bitmapfont (otb conversion). Hand-write the pilot manifest entries plus a family.toml per family (form/vibes/homepage filled in carefully); get the full pipeline running end to end, the site build passing, and e2e all green; record UnifontEX's build time and artifact size in the report.
- [x] **Step 5: commit** `feat: import tooling and five pilot families` (fonts/ and the generated report land together)

### Task 21: TTF rasterization conversion

**Files:**
- Create: `pipeline/opf/ingest/rasterize.py`, `pipeline/tests/test_rasterize.py`

**Interfaces:**
- Produces: `detect_native_ppem(ttf: Path) -> int | None` (outline grid GCD: sample ≤200 glyphs and take the common divisor of all on-curve coordinates against the em, with `em/gcd` as the candidate; cross-checked against name/upem heuristics, returning None on disagreement); `rasterize_ttf(ttf: Path, ppem: int) -> ParsedFont` (freetype-py `FT_LOAD_TARGET_MONO|FT_LOAD_RENDER`, converting the bitmap into Glyph objects); `verify_sheet(f: ParsedFont, out: Path)` (render a comparison PNG of representative characters for manual spot checks).

- [x] **Step 1: failing tests**: for a pixel TTF from the collection folder known to be natively 12px (e.g. the fusion-pixel ttf if present, otherwise ChillBitmap), `detect_native_ppem` == the nominal value; after rasterization the ink of "A" matches that family's official BDF (where one exists); an ordinary TTF with no grid regularity (the system DejaVu if present, otherwise skip) returns None.
- [x] **Step 2–4: fail → implement → pass** → **Step 5: commit** `feat: TTF native grid detection and rasterization`

### Task 22: Full import and curation

**Files:**
- Modify: `ingest/manifest.toml` (entries for the whole collection folder, written after checking each directory: source priority release-BDF > repo BDF > OTB/kbitx > TTF conversion; PNG / C-header families go into todo after a duplicate check)
- Create/Modify: each `fonts/<slug>/family.toml` (form prefilled with a suggested value plus a `# UNVERIFIED` comment; vibes, homepage, provenance filled in for real)
- Modify: `docs/import-report.md` (the full report plus the style-annotation review list)

- [x] **Step 1: write the manifest and import in batches (Chinese→Japanese→Korean→Pan-CJK→supplement); for each batch: a full pipeline build, pytest/vitest/e2e all green, a manual visual spot check of 3 family detail pages, and one commit** (commit `feat: import <batch name> families`)
- [x] **Step 2: size check**: record the totals for `site/public/data` and `dist-downloads` in the report; if data exceeds 700MB, activate the trimming contingency (defer rare SMP chunks to Release hosting) and record it
- [x] **Step 3: full e2e + a rebuild cache hit-rate check; commit** `feat: full import complete and import report`

## Phase D — Polish and Launch

### Task 23: Visual polish and human-sounding copy

- [x] **Step 1: load the frontend-design skill and polish the whole site against the principles in spec §8 (typographic details, focus states, empty states, loading skeletons, dark-mode review, mobile breakpoints)**; commit the e2e snapshots (Playwright screenshot baselines)
- [x] **Step 2: load the humanizer skill and run it over all the Chinese copy; changes to the English copy are reviewed by an Opus/Sonnet subagent**
- [x] **Step 3: verify the performance budget: catalogue page first-screen JS < 150KB gz (`ls dist` totals + Playwright network recording); first canvas paint < 1s (timed against a local preview)**
- [x] **Step 4: commit** `feat: visual and copy polish`

### Task 24: CI and release

**Files:**
- Create: `.github/workflows/ci.yml` (PR: py-test + ts-test + astro build), `.github/workflows/deploy.yml` (push to main: pipeline (actions/cache keyed on the fonts hash) → astro build → upload-pages-artifact → deploy-pages; downloadables via `gh release upload downloads --clobber`, incrementally by manifest sha)
- Modify: `README.md` (complete usage instructions: adding a font, family.toml, local builds, deployment)

- [x] **Step 1: statically validate the workflows locally (yaml lint plus a step-by-step check of action versions if `act` is unavailable)**
- [x] **Step 2: write the README (in Chinese, with a short English version)** → **Step 3: commit** `chore: CI workflows and README`

### Task 25: Final verification

- [x] **Step 1: load superpowers:verification-before-completion; time a cold end-to-end build (target < 15 minutes), run all tests, check the size red line, and check for broken links (an internal link crawler script)**
- [x] **Step 2: walk through the spec section by section (ticking off each success criterion in §1) and backfill any gaps**
- [x] **Step 3: request a code review (/code-review or the requesting-code-review skill) and fix the findings**
- [x] **Step 4: commit** `chore: final pre-release verification`

---

## Self-Review Record

- **Spec coverage**: §3 directory conventions→T1/T8; §4.1→T2 (PCF parsing is scheduled after T2 as a follow-up: see "Additional task" below); §4.2→T3; §4.3→T4/5/6; §4.4→T7; §4.5→T9/10; §4.6→T12; §4.7→T13/24; §4.8→T14/18; §5→T15–19; §6→T20–22; §7→T4/5/6/18; §8→T15/23; §9→T1/24; §10 ordering = Phases A–D; §11 risks→T20 stress test / T22 trimming contingency / T21 verification.
- **Gap found: no task for the PCF parser** → added Task 2b.
- **Type consistency**: C1–C8 are the sole authority; every task signature references the contracts and has been re-checked for consistency (`GlyphChunk.size` is uniformly the glyph count; `InkMetrics.max_ink_cps` is mapped to `maxInkCps` when emitted per C6).

### Task 2b: PCF parser (executed after Task 2)

**Files:**
- Create: `pipeline/opf/parsers/pcf.py`, `pipeline/tests/test_pcf.py`, fixture: `pipeline/tests/fixtures/mini.pcf` (generated by `bdftopcf mini.bdf` and committed)

**Interfaces:**
- Produces: `parse_pcf(path: Path, family_slug: str) -> ParsedFont` (the properties/metrics/bitmaps/encoding/glyph-names tables; byte order / bit order / scan-unit handling; ISO10646 encoding tables pass through directly, gb2312/jisx0208/ksc5601/big5 are mapped via Python codecs, and an unknown registry records a warning and drops the unmapped glyphs).

- [x] **Step 1: failing tests**: `parse_pcf(mini.pcf)` matches `parse_bdf(mini.bdf)` field for field on every glyph (cp/dwidth/bbw/bbh/rows); both the compressed and uncompressed metrics branches are covered (generate a second fixture with `bdftopcf -t`).
- [x] **Step 2–5: fail → implement → pass → commit** `feat: PCF parser`
