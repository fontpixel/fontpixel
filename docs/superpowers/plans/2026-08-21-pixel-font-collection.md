# 开源像素字体馆 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从 `fonts/` 目录自动构建的双语静态点阵字体目录站,含覆盖率报告、canvas 像素样例、BDF/PCF 下载与批量导入工具。

**Architecture:** Python 管线(解析 BDF/PCF → 度量/覆盖率/许可证 → 字形二进制包 + SVG 预渲染 + 下载物 + JSON 索引)产出到 `site/public/data/`;Astro 5 SSG 双语站点用 Svelte 5 岛屿消费这些数据,canvas 逐像素渲染样例;下载物由 CI 传 GitHub Releases。

**Tech Stack:** Python 3.12 + fonttools + freetype-py + Pillow + pytest;Node 24 + Astro 5 + Svelte 5 + TypeScript strict + vitest + Playwright;bdftopcf。

**Spec:** `docs/superpowers/specs/2026-08-21-open-pixel-fonts-design.md`(本计划从该 spec 论证;执行者两者都读)

> **进度(2026-08-21)**:Task 1–21 已完成并逐一提交;Task 24(CI/README)已完成;
> Task 22 进行中(试点五家族已上线,全量清单由并行代理起草中);Task 23、25 待做。
> 逐任务提交历史即为追踪记录(git log --oneline)。

## Global Constraints

- 站点 Pages 产物 ≤ 900MB(构建脚本硬检查);目录页首屏 JS < 150KB gz。
- 核心包 ≤ 8KB gz/变体;分块目标 ≤ 16KB gz,原始上限 48KB。
- 全部 UI 文案中文先行;**英文翻译一律由 Opus/Sonnet 子代理产出与复核(全局规则,Fable 不得直译)**。
- TDD:每个功能先写失败测试;提交格式 `<type>: <中文摘要>`(feat/fix/test/docs/chore/refactor)。
- 字表数据文件必须带头部注释:来源、版本、获取日期、许可;第三方数据登记 `THIRD_PARTY_NOTICES.md`。
- 管线确定性:同输入同输出(字典序遍历、固定 gzip mtime=0);增量缓存键 = 文件 sha256 + PIPELINE_VERSION。
- Python 包名 `pfc`(位于 `pipeline/`,`pip install -e pipeline`);站点库代码 `site/src/lib/`。
- 站点 base 路径可配(`OPF_BASE`,默认 `/open-pixel-fonts`);所有 fetch 经 `withBase()`。
- 旧项目代码仅作参考,不复制;旧项目 `scripts/data/cjk-tables/*.txt` 数据文件可迁移(MIT,保留声明)。

---

## 共享契约(所有任务的权威定义)

### C1. 字形包二进制格式 v1(little-endian)

一个文件 = 一个分块(chunk),覆盖码位区间 `[rangeStart, rangeEnd)`。核心包同格式,区间 `[0, 0x110000)`,稀疏存储。落盘为 gzip(`.bin.gz`,mtime=0)。

```
偏移  类型   字段
0     4B    magic = "PFG1"
4     u8    version = 1
5     u8    flags = 0(保留)
6     u16   glyphCount
8     u32   rangeStart
12    u32   rangeEnd
16    glyphCount × 14B 索引项(按 cp 升序):
        u32 cp
        i16 dwidth        (x 方向 advance, px)
        u8  bbw, u8 bbh   (位图宽高 px)
        i8  bbxoff, i8 bbyoff (BDF BBX 偏移)
        u32 bitmapOffset  (相对位图区起点)
之后  位图区:每字形 bbh × ceil(bbw/8) 字节,行序自上而下,位 MSB-first(BDF 约定)
```

### C2. 变体 manifest(`data/packs/<slug>/<variantId>/manifest.json`)

```json
{ "version": 1, "slug": "galmuri", "variantId": "Galmuri9",
  "pixelSize": 9, "ascent": 8, "descent": 1, "glyphCount": 12000,
  "core": { "file": "core.bin.gz", "gzBytes": 6100, "glyphs": 320 },
  "ranges": [ { "start": 0, "end": 256, "file": "00000000-00000100.bin.gz",
                "gzBytes": 1500, "glyphs": 95 } ] }
```

### C3. Python 内部模型(`pfc/model.py`)

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
    glyphs: list[Glyph]             # cp 升序,仅 ENCODING>=0
    warnings: list[str]
```

### C4. TS 解码与渲染接口(`site/src/lib/`)

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
  constructor(dataBase: string)   // 如 `${base}/data`
  loadManifest(slug: string, variantId: string): Promise<VariantManifest>
  glyphsFor(slug: string, variantId: string, text: string): Promise<Map<number, DecodedGlyph | null>>
}
// render.ts — 纯函数光栅化到 1:1 缓冲,再由 canvas 封装放大(imageSmoothing 关)
export interface RenderOpts { scale: number; invert: boolean; grid: boolean;
  highlightMissing: boolean; maxWidth?: number }
export interface RasterResult { width: number; height: number;
  data: Uint8ClampedArray /* RGBA */; missing: number[] }
export function rasterize(text: string, glyphs: Map<number, DecodedGlyph | null>,
  font: { pixelSize: number; ascent: number; descent: number },
  opts: Omit<RenderOpts, "scale">): RasterResult
export function paint(canvas: HTMLCanvasElement, r: RasterResult, scale: number): void
```

缺字排版:advance = round(pixelSize/2)+1,基线上画 ascent 高的 1px 虚线框;`highlightMissing` 时填充高亮色。换行仅 `\n`;无 shaping/kerning(关于页注明)。

### C5. index.json(目录页;`data/index.json`)

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

`confidence ∈ {"auto-high","auto-low","manual","unknown"}`。`form ∈ {gothic,mingcho,rounded,kai,fangsong,serif-pixel,sans,script,decorative,terminal,other,""}`(空=未分类)。`scripts ⊆ {zh-hans,zh-hant,ja,ko,latin,cyrillic,greek}`。

### C6. detail.json(`data/details/<slug>.json`)

```json
{ "slug": "galmuri", "meta": { "...同 index 家族项..." : 0 },
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

### C7. 覆盖率字表注册(`pfc/coverage/charsets.py` + `pfc/coverage/data/`)

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

数据文件格式(`pfc/coverage/data/<section>/<id>.txt`):

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

行格式三选一:`XXXX`(hex)、`XXXX..YYYY`(闭区间)、原字面字符(每行任意个,逐字符取)。`#` 注释。

### C8. 目录规约与产物路径

```
site/public/data/
  index.json
  coverage-intervals.bin.gz        # 查字:见 Task 18
  details/<slug>.json
  packs/<slug>/<variantId>/{manifest.json, core.bin.gz, XXXXXXXX-XXXXXXXX.bin.gz}
  previews/<slug>/<lang>.svg       # 构建期默认样例 SVG
  og/<slug>.png
dist-downloads/
  manifest.json                    # [{family,variantId,kind,file,bytes,sha256}]
  galmuri--Galmuri9.bdf.gz / .pcf.gz / galmuri.zip
```

`variantId` = 文件名去扩展名,仅 `[A-Za-z0-9_-]`(其余替换 `-`)。`slug` = 家族目录名。

---

## Phase A — 管线核心

### Task 1: 仓库脚手架

**Files:**
- Create: `.gitignore`, `Makefile`, `README.md`
- Create: `pipeline/pyproject.toml`, `pipeline/opf/__init__.py`(`PIPELINE_VERSION = 1`), `pipeline/tests/test_smoke.py`
- Create: `site/package.json`, `site/astro.config.mjs`, `site/tsconfig.json`, `site/svelte.config.js`, `site/vitest.config.ts`, `site/src/lib/version.ts`, `site/src/lib/version.test.ts`, `site/src/pages/index.astro`(临时占位)

**Interfaces:**
- Produces: `make py-test`(pipeline pytest)、`make ts-test`(site vitest)、`make dev`、`make build`;Python venv `.venv`;`import opf` 可用。

- [x] **Step 1: Python 侧脚手架 + 冒烟测试**

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

- [x] **Step 2: 创建 venv 并验证 pytest 通过**

```bash
python3 -m venv .venv && .venv/bin/pip -q install -e "pipeline[dev]"
.venv/bin/pytest pipeline/tests -q   # 期望 1 passed
```

- [x] **Step 3: 站点脚手架(Astro5+Svelte5+TS strict+vitest)+ 冒烟测试**

`site/src/lib/version.ts` 导出 `export const SITE_VERSION = 1`;`version.test.ts` 断言之。`npm create astro` 交互不可用,手写最小 `package.json`(deps: astro@^5, @astrojs/svelte@^7, svelte@^5;dev: typescript, vitest, playwright 于 Task 15 再加)与 `astro.config.mjs`(svelte 集成,`base: process.env.OPF_BASE ?? '/open-pixel-fonts'`)。

- [x] **Step 4: 验证 `npm install && npx vitest run` 通过、`npx astro build` 成功**

- [x] **Step 5: Makefile(fonts/dev/build/py-test/ts-test/test 目标)与 .gitignore(`.venv/ node_modules/ dist/ .cache/ site/public/data/ dist-downloads/ __pycache__/`),提交**

```bash
git add -A && git commit -m "chore: 仓库脚手架(pfc 包 + Astro/Svelte 站点)"
```

### Task 2: BDF 解析器

**Files:**
- Create: `pipeline/opf/model.py`(契约 C3)、`pipeline/opf/parsers/__init__.py`、`pipeline/opf/parsers/bdf.py`
- Create: `pipeline/tests/fixtures/mini.bdf`(手工构造,3 字形:A、汉字「永」、组合符)、`pipeline/tests/test_bdf.py`

**Interfaces:**
- Produces: `parse_bdf(path: Path, family_slug: str) -> ParsedFont`;`.bdf.gz` 透明解压;非致命问题进 `ParsedFont.warnings`。

- [x] **Step 1: 写 fixture 与失败测试**

`mini.bdf` 内容(完整写入,含 `SIZE 16 75 75`、`FONTBOUNDINGBOX 16 16 0 -2`、`PIXEL_SIZE 16`、`FONT_ASCENT 14`、`FONT_DESCENT 2`,字形 `A`(ENCODING 65, DWIDTH 8 0, BBX 7 10 0 0)、`uni6C38`(ENCODING 27704, DWIDTH 16 0, BBX 16 15 0 -1)、一个 ENCODING -1 字形应被跳过)。

`test_bdf.py` 核心断言:

```python
from pathlib import Path
from opf.parsers.bdf import parse_bdf
FIX = Path(__file__).parent / "fixtures"

def test_parse_mini_bdf():
    f = parse_bdf(FIX / "mini.bdf", "mini")
    assert f.pixel_size == 16 and f.ascent == 14 and f.descent == 2
    assert f.bbox == (16, 16, 0, -2)
    assert [g.cp for g in f.glyphs] == [65, 27704]      # -1 被跳过,升序
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
    f = parse_bdf(FIX / "mini-bad.bdf", "mini")          # BITMAP 行长度不符
    assert any("bitmap" in w.lower() for w in f.warnings)
```

- [x] **Step 2: 运行确认失败(模块不存在)**:`.venv/bin/pytest pipeline/tests/test_bdf.py -q`

- [x] **Step 3: 实现 `bdf.py`**

要点:逐行状态机(header → properties → chars);`ENCODING` 取十进制,负值跳过但计数;`BITMAP` 十六进制行按 `ceil(bbw/8)` 字节截断/补零并记警告;重复 ENCODING 保留首个记警告;`SIZE` pt@dpi → px = round(pt × dpi/72) 仅当无 `PIXEL_SIZE`;缺 `FONT_ASCENT/DESCENT` 时从 `FONTBOUNDINGBOX` 推(ascent = h+yoff… ascent = bbox_h + bbox_yoff, descent = -bbox_yoff)并记警告;`open` 分支:后缀 `.gz` 用 `gzip.open`;编码按 latin-1 读(BDF 属性可能含非 ASCII)。

- [x] **Step 4: 测试通过后,用收集夹真实字体做集成断言(拷入 fixture)**

```bash
cp "/home/chen/githubprojects/pixelfontworkshop/pixel-font-collection-fonts/CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/quiple--galmuri/dist/Galmuri7.bdf" pipeline/tests/fixtures/real-galmuri7.bdf
```

追加测试:字形数 >1000、全部 `len(rows)==bbh*ceil(bbw/8)`、cp 严格递增。

- [x] **Step 5: 全部通过,提交** `feat: BDF 解析器`

### Task 3: 尺寸与墨迹度量

**Files:**
- Create: `pipeline/opf/metrics.py`、`pipeline/tests/test_metrics.py`

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
def glyph_ink_size(g: Glyph) -> tuple[int, int] | None   # 点亮像素外接框 (w,h);空=None
def compute_ink(f: ParsedFont, han_ref: frozenset[int]) -> InkMetrics
def is_monospaced(f: ParsedFont) -> bool                 # ≥99% 字形同 dwidth
def claimed_size(f: ParsedFont) -> int
```

- [x] **Step 1: 失败测试**(构造 `Glyph` 直接测)

```python
def _g(cp, w, h, bits):  # bits: list[str] 如 ["0100000","1110000"]
    rows = bytes(int(r.ljust((len(r)+7)//8*8, "0"), 2).to_bytes((len(r)+7)//8, "big")[i]
                 for r in bits for i in range((len(r)+7)//8))
    return Glyph(cp=cp, name=f"u{cp:x}", dwidth=w, bbw=w, bbh=h, bbx=0, bby=0, rows=rows)

def test_ink_bbox_trims_margins():
    g = _g(0x4E00, 8, 8, ["00000000","00111100","00100100","00111100",
                          "00000000","00000000","00000000","00000000"])
    assert glyph_ink_size(g) == (4, 3)

def test_empty_glyph_none():
    assert glyph_ink_size(_g(32, 8, 8, ["00000000"]*8)) is None

def test_han_ink_median():  # 三个汉字墨迹 (14,14),(15,15),(16,16) → 中位 (15,15)
    ...
def test_monospace_tolerance():  # 100 字形 99 个 dwidth=8、1 个 4 → True;95/5 → False
    ...
```

(`test_han_ink_median`/`test_monospace_tolerance` 按上式用 `_g` 构造完整写出。)

- [x] **Step 2: 运行确认失败** → **Step 3: 实现**(median 用 `statistics.median_low`;han_ref 交集 <100 时回退全部 U+4E00–9FFF∪扩展区字形;cap = A–Z 墨迹高中位,x = a–z 中「acemnorsuvwxz」墨迹高中位) → **Step 4: 通过** → **Step 5: 提交** `feat: 宣称/墨迹度量`

### Task 4: 字表数据基础(编解码派生 + 旧数据迁移 + UCD)

**Files:**
- Create: `pipeline/opf/coverage/__init__.py`、`charsets.py`(契约 C7)、`ucd.py`
- Create: `pipeline/opf/coverage/gen/gen_codec_tables.py`(生成器,提交生成物)
- Create: `pipeline/opf/coverage/data/…`(生成/迁移的 .txt)、`pipeline/opf/coverage/data/ucd/`(Blocks.txt + assigned-ranges.txt)
- Create: `pipeline/tests/test_charsets.py`、`THIRD_PARTY_NOTICES.md`
- 迁移:`cp ../open-pixel-fonts-old/scripts/data/cjk-tables/*.txt` → 转换为 C7 格式入 `data/`(gb12345、tongyong-guifan(整表)、7000tongyong、3500changyong、yiwu-jiaoyu、guji、iicore、hanyi、fangzheng、4808、6343、big5changyong、big5、hkchangyong、hkscs、suppchara)

**Interfaces:**
- Produces: `load_charsets(data_dir) -> list[Charset]`;`Ucd`(`blocks: list[tuple[str,int,int]]`、`assigned: frozenset[int]`、`block_assigned_counts`);生成器可重跑且幂等。

- [x] **Step 1: 失败测试 — 已知常数断言**

```python
def test_known_counts():
    cs = {c.id: c for c in load_charsets(DATA)}
    assert len(cs["gb2312-l1"].cps) == 3755
    assert len(cs["gb2312-l2"].cps) == 3008
    assert len(cs["big5-changyong"].cps) == 5401
    assert len(cs["ksx1001-hangul"].cps) == 2350
    assert len(cs["ksx1001-hanja"].cps) == 4888          # 重复汉字按码位去重后 4620,断言取实际生成值并注明
    assert len(cs["jisx0208-l1"].cps) == 2965
    assert len(cs["jisx0208-l2"].cps) == 3390
    assert len(cs["hiragana"].cps) == 86                  # U+3041..3096 + 309D..309F 按定义文件
    assert len(cs["kangxi-radicals"].cps) == 214
    assert len(cs["cp437"].cps) == 256
def test_loader_formats(tmp_path):
    # 写含 hex/区间/字面三种行的临时表,断言解析并集正确
    ...
def test_every_table_has_metadata():
    for c in load_charsets(DATA):
        assert c.name_zh and c.name_en and c.source
def test_ucd_blocks():
    u = load_ucd(DATA / "ucd")
    assert ("Basic Latin", 0x0000, 0x007F) in u.blocks
    assert u.block_assigned_counts["Basic Latin"] == 128
```

注:生成器运行后若与常数断言冲突(如 ksx1001-hanja 去重),以权威来源修正断言并在数据头注明口径,再提交。

- [x] **Step 2: 确认失败** → **Step 3: 实现 loader + 生成器**

生成器要点:GB2312 一/二级按区位(区 16–55 / 56–87)经 `bytes([0xA0+r, 0xA0+c]).decode('gb2312')`;Big5 常用 A440–C67E、次常用 C940–F9D5 经 `big5` codec;JIS X 0208 水準按区(1–8 非汉字、16–47 一水準、48–84 二水準)经 `euc_jp`;JIS X 0213 三/四水準经 `euc_jis_2004`(面区位枚举,三水準=面1新增区,四水準=面2);KS X 1001 谚文区 16–40、汉字区 42–93 经 `euc_kr`;GBK 汉字与 GB18030 全汉字经 `gb18030` codec 枚举。假名/注音/部首/盲文/制表/方块/Powerline(U+E0A0–E0A2,U+E0B0–E0B3 基本 + U+E0A3,U+E0B4–E0D4 扩展)/半角假名/JIS X 0201/谚文音节与字母:直接区间写数据文件。UCD:下载 Unicode 17.0 `Blocks.txt` + `UnicodeData.txt` 生成 `assigned-ranges.txt`(网络不可用则退 Python `unicodedata` 并在 source 注明版本)。旧数据迁移脚本一次性转换格式并保留 CJK-character-count MIT 声明于 `THIRD_PARTY_NOTICES.md`。

- [x] **Step 4: 通过** → **Step 5: 提交** `feat: 字表数据基础与 UCD(编解码派生+迁移)`

### Task 5: 外部字表获取(联网研究,产物离线提交)

**Files:**
- Create: `pipeline/opf/coverage/data/jp/joyo-2136.txt`、`jp/kyoiku-1026.txt`、`jp/jinmeiyo.txt`、`gb/gb18030-2022-l1.txt`、`-l2.txt`、`-l3.txt`、`intl/unihan-core-2020.txt`、`intl/wgl4.txt`、`intl/viet-latin.txt`、`prc-lit/tongyong-guifan-l1/-l2/-l3.txt`、`prc-lit/changyong-2500.txt`、`prc-lit/cichangyong-1000.txt`
- Modify: `pipeline/tests/test_charsets.py`(追加计数断言)、`THIRD_PARTY_NOTICES.md`

**Interfaces:**
- Produces: 上述表进入 `load_charsets` 结果;每表头部含权威来源引用。

- [x] **Step 1: 追加失败断言**(joyo=2136、kyoiku=1026、tongyong-guifan l1+l2+l3=8105、changyong-2500+cichangyong-1000=3500、wgl4=652;GB18030-2022 级别数取标准原文,研究后填入)
- [x] **Step 2: 逐表联网检索权威来源(标准原文/官方公报/Unicode Unihan kUnihanCore2020、kIICore)→ 生成数据文件(可派发并行子代理分头取数,结果回本任务统一校验)**
- [x] **Step 3: 断言通过;来源写入文件头与 THIRD_PARTY_NOTICES**
- [x] **Step 4: 提交** `feat: 规范字表与国际字表数据`

### Task 6: 覆盖率引擎

**Files:**
- Create: `pipeline/opf/coverage/engine.py`、`pipeline/tests/test_coverage.py`

**Interfaces:**
- Consumes: `Charset`、`Ucd`、`ParsedFont`
- Produces:

```python
def font_cps(f: ParsedFont) -> frozenset[int]
def coverage_for(cps, charsets) -> dict[str, tuple[int, int]]
def unicode_block_coverage(cps, ucd) -> list[tuple[str, int, int]]   # 仅 have>0 的块,加„全表模式"参数
def overview(cps, ucd) -> dict   # total/planes/pua3/han_total/compat(含12字脚注数据)
def badges(cov: dict[str, tuple[int,int]]) -> list[str]              # 阈值:见 spec §7 徽章
def detect_scripts(cov) -> list[str]                                  # 阈值:gb2312-l1≥50%→zh-hans; big5-changyong≥50%→zh-hant; hiragana&katakana≥90%→ja; ksx1001-hangul≥50%→ko; latin-basic≥90%→latin
```

- [x] **Step 1: 失败测试**(合成 cps 集:全 GB2312 一级 → `coverage_for` 该表 (3755,3755) 且 badges 含 `gb2312`… 每分支一个用例,含 compat 12 字脚注、PUA 三区)
- [x] **Step 2: 失败确认** → **Step 3: 实现** → **Step 4: 通过** → **Step 5: 提交** `feat: 覆盖率引擎`

### Task 7: 许可证识别

**Files:**
- Create: `pipeline/opf/licenses.py`、`pipeline/opf/licenses_data/`(已知许可证规范文本片段)、`pipeline/tests/test_licenses.py`、`pipeline/tests/fixtures/licenses/`(从收集夹复制 OFL.txt、MIT、Apache、IPA、M+、Baekmuk 等真实文本)

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

- [x] **Step 1: 失败测试**:每种真实文本 → 期望 spdx 与 `auto-high`;仅 BDF `COPYRIGHT` 提示 → `auto-low`;toml 覆写全胜 → `manual`;啥都没有 → `unknown`。识别法:归一化(小写、压空白、去版权行)后按**特征短语组**匹配(如 OFL-1.1 需同时含 "sil open font license" 与 "version 1.1";GPL+FE 需含 "font exception"),不可用整文 hash(版权行可变)。
- [x] **Step 2–5: 失败→实现→通过→提交** `feat: 许可证识别(指纹+三级置信)`

### Task 8: family.toml 与变体解析

**Files:**
- Create: `pipeline/opf/familymeta.py`、`pipeline/tests/test_familymeta.py`

**Interfaces:**
- Consumes: `ParsedFont`、`LicenseInfo`
- Produces:

```python
@dataclass
class VariantDesc:
    id: str; file: str; size: int; weight: str; spacing: str
    script_subset: str | None; display: str
@dataclass
class FamilyMeta:  # 解析 toml + 缺省推导后的完整视图
    slug: str; name: str; name_zh: str; author: str; homepage: str
    repository: str; description: str; form: str; vibes: list[str]
    converted_from: str; provenance: str; curated: bool
    license_override: dict | None; samples: dict[str, str]
    variant_overrides: dict[str, dict]
def load_family_meta(family_dir: Path) -> FamilyMeta        # 无 toml → stub 写盘 + curated=False
def resolve_variant(f: ParsedFont, meta: FamilyMeta) -> VariantDesc
```

- [x] **Step 1: 失败测试**:完整 toml 解析;无 toml 生成 stub(内容含 TODO 注释,name=目录名 title-case)且 `curated=False`;变体推导:`WEIGHT_NAME=Bold`→bold,文件名含 `-bold`→bold,`SPACING∈{C,M}`→monospaced,文件名 `zh_hans`→`zh-hans`;`[variants]` 覆写全胜;`variantId` 非法字符替换。
- [x] **Step 2–5: 失败→实现(`tomllib` 读,stub 用字符串模板写)→通过→提交** `feat: family.toml 与变体解析`

### Task 9: 字形包写入器

**Files:**
- Create: `pipeline/opf/glyphpack.py`、`pipeline/tests/test_glyphpack.py`

**Interfaces:**
- Consumes: `ParsedFont`、`VariantDesc`;契约 C1/C2/C8
- Produces:

```python
CORE_TEXT: str  # 可打印 ASCII + 平/片假名 + 谚文兼容字母 + 全部默认样例句(spec §5.2)用字
def plan_chunks(cps: list[int]) -> list[tuple[int, int]]   # 对齐 256 块;gap>16 块断开;原始预估>48KB 断开
def write_packs(f: ParsedFont, v: VariantDesc, meta_name: str, out_dir: Path) -> dict  # 返回 manifest dict 并落盘
def read_chunk(path: Path) -> list[Glyph]                  # Python 侧读回,供测试与跨语言夹具
```

- [x] **Step 1: 失败测试**:mini 字体 → manifest 区间正确;`read_chunk(write(…))` 往返逐字段相等;字节级黄金断言(mini 字体 chunk 的前 16 字节 == `b"PFG1\x01\x00\x02\x00..."`);确定性(两次写入 sha256 相同,gzip mtime=0);核心包含家族名用字;真实 galmuri fixture:全部 chunk gz ≤16KB(允许列出豁免:单块 256 cp 全满的 32×64 字体上限受控于 48KB 原始断块)。
- [x] **Step 2–5: 失败→实现(`struct.pack("<IHH…")` 风格;分块贪心合并)→通过→提交** `feat: 字形包 v1 写入器`

### Task 10: TS 字形包解码器

**Files:**
- Create: `site/src/lib/glyphpack.ts`、`site/src/lib/glyphpack.test.ts`、`site/src/lib/decompress.ts`
- Create: `site/src/lib/__fixtures__/mini-chunk.bin`(由 Task 9 的 Python writer 在测试中生成后拷入,提交)

**Interfaces:**
- Consumes: C1 二进制;Produces: C4 `GlyphChunk`。`decompress.ts`:`gunzip(buf: ArrayBuffer): Promise<ArrayBuffer>` 用 `DecompressionStream`,Node 测试环境用 `node:zlib` 分支。

- [x] **Step 1: 失败测试**

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

- [x] **Step 2–5: 失败→实现(DataView + 二分查找)→通过→提交** `feat: TS 字形包解码器(跨语言契约测试)`

### Task 11: 纯函数光栅化与 canvas 绘制

**Files:**
- Create: `site/src/lib/render.ts`、`site/src/lib/render.test.ts`

**Interfaces:** 契约 C4(`rasterize`/`paint`/`RenderOpts`/`RasterResult`)。

- [x] **Step 1: 失败测试**:单字形 A(用 Task 10 夹具)→ 输出尺寸 = (dwidth, ascent+descent);位 (x,y) 对应像素黑;invert 后反色;缺字返回 `missing:[cp]` 且占位框宽 = round(16/2)+1;`\n` 断行;`maxWidth` 词内断行;grid 选项在缩放≥4 时画网格线(rasterize 不管 grid——grid 属 paint 层,测试只测 rasterize 数据正确)。
- [x] **Step 2–5: 失败→实现(rasterize 纯 TS 输出 RGBA;paint 用 `putImageData` 到离屏 1:1 再 `drawImage` 放大,`imageSmoothingEnabled=false`)→通过→提交** `feat: 像素光栅化与绘制`

### Task 12: SVG 预渲染与 og 图

**Files:**
- Create: `pipeline/opf/prerender.py`、`pipeline/tests/test_prerender.py`

**Interfaces:**
- Consumes: `ParsedFont`、样例句常量 `SAMPLES: dict[str, str]`(spec §5.2 默认句,定义于本模块,`glyphpack.CORE_TEXT` 引用之)
- Produces: `sample_svg(f, text, fg="#1a1a1a") -> str`(rect 水平连游程合并,viewBox=1:1 像素,`shape-rendering="crispEdges"`);`og_png(f, name, text, out: Path)`(1200×630,Pillow,像素放大最近邻)。

- [x] **Step 1: 失败测试**:mini 字体 "A" → SVG rect 数 == A 的水平游程数;viewBox 宽 == dwidth;缺字出现占位 rect(带 `class="missing"`);og 输出 PNG 尺寸 1200×630。
- [x] **Step 2–5: 失败→实现→通过→提交** `feat: SVG 预渲染与 og 卡片`

### Task 13: 下载物构建

**Files:**
- Create: `pipeline/opf/downloads.py`、`pipeline/tests/test_downloads.py`

**Interfaces:**
- Produces: `build_downloads(families: list[BuiltFamily], out: Path) -> dict`(manifest;`BuiltFamily` 见 Task 14)。产物按 C8:`<slug>--<variantId>.bdf.gz`、`.pcf.gz`(`bdftopcf` 子进程,失败记警告仅出 bdf)、`<slug>.zip`(BDF 原文 + 许可证 + README.txt 含 provenance)。gzip/zip 时间戳固定(1980-01-01)保证确定性。

- [x] **Step 1: 失败测试**(mini 家族 → 三类产物存在、sha256 与 manifest 一致、zip 内含 LICENSE 与 README.txt、重跑字节相同;`shutil.which("bdftopcf")` 缺失时跳过 pcf 断言)
- [x] **Step 2–5: 失败→实现→通过→提交** `feat: BDF/PCF/zip 下载物与 manifest`

### Task 14: 构建编排器与索引产出

**Files:**
- Create: `pipeline/opf/build.py`(入口 `python -m opf.build`)、`pipeline/opf/emit.py`、`pipeline/opf/cache.py`、`pipeline/tests/test_build.py`
- Create: `pipeline/tests/fixtures/fonts-tree/`(两个家族:mini + galmuri 真实文件,含一个无 toml 家族)
- Create: `site/src/lib/schema.ts`(zod)与 `site/src/lib/schema.test.ts`

**Interfaces:**
- Consumes: Task 2–13 全部
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

CLI:`--fonts fonts/ --out site/public/data --downloads dist-downloads --cache .cache [--family <slug>]`。emit 按 C5/C6/C8 输出;`badges`/`scripts`/`sampleLang` 用 Task 6 函数;缓存:家族级,键=全部源文件 sha256+PIPELINE_VERSION,命中即跳过重算(产物已在盘上)。体积红线:结束时统计 `site/public/data` 总量,>900MB 退出码 2。

- [x] **Step 1: 失败测试**:fixtures-tree 全量构建 → index.json 家族数 2、无 toml 家族 `curated:false` 且 stub 已写、details/packs/previews/og/downloads 齐全、二次构建缓存命中(mtime 不变且日志含 "cached")、`--family` 只重建单家族。
- [x] **Step 2: zod schema 测试**:`schema.ts` 定义 C5/C6 的 zod 模型;vitest 读取 pytest 产出的 fixture index.json(提交一份到 `site/src/lib/__fixtures__/index.fixture.json`)校验通过——跨语言契约。
- [x] **Step 3–5: 失败→实现→通过→提交** `feat: 构建编排器、索引产出与增量缓存`

## Phase B — 站点

### Task 15: Astro 骨架、i18n、主题基座

**Files:**
- Create: `site/src/i18n/{types.ts,zh.ts,en.ts,index.ts}`(`t(lang)` 取词;`en.ts` 由 Opus/Sonnet 子代理翻译产出)
- Create: `site/src/layouts/Base.astro`(html lang、hreflang alternate、theme 切换脚本、header/footer、设计令牌 CSS)
- Create: `site/src/styles/tokens.css`(纸白/炭黑双主题变量、朱砂红 accent、间距/字号阶)
- Create: `site/src/pages/index.astro`(语言跳转页)、`site/src/pages/[lang]/index.astro`(目录页壳)、`site/src/pages/[lang]/about.astro`、`site/src/pages/404.astro`
- Create: `site/src/lib/data.ts`(`loadIndex()` 构建期 fs 读 `site/public/data/index.json`;`withBase(path)`)
- Create: `site/e2e/smoke.spec.ts`、`site/playwright.config.ts`;Modify: `site/package.json`(加 playwright)

**Interfaces:**
- Consumes: Task 14 产物(fixture 数据构建)
- Produces: `UIStrings` 接口与 `t()`;`Base.astro` slot 布局;`withBase`;e2e 基座(`npx playwright test`,webServer 起 `astro preview`)。

- [x] **Step 1: 用 fixtures 跑管线生成 `site/public/data/`**:`.venv/bin/python -m opf.build --fonts pipeline/tests/fixtures/fonts-tree --out site/public/data --downloads dist-downloads --cache .cache`
- [x] **Step 2: 失败 e2e**:`/zh/` 200 且含站名「开源像素字体馆」、html[lang=zh]、hreflang en 链接存在;`/en/` 英文站名;`/` 跳转脚本存在;暗色切换写 localStorage 且 html[data-theme] 变化。
- [x] **Step 3: 实现骨架与样式基座(令牌:`--bg`纸白/`--ink`炭黑/`--accent`朱砂红 #c3272b 系,dark 反转;进度条方块与 1px 分隔线组件类)**
- [x] **Step 4: 派发 Opus/Sonnet 子代理翻译 `zh.ts` → `en.ts`(含复核);本任务内完成集成**
- [x] **Step 5: e2e 通过;提交** `feat: 站点骨架、双语路由与主题基座`

### Task 16: 目录页(筛选、卡片、全局样例)

**Files:**
- Create: `site/src/lib/filters.ts`、`site/src/lib/filters.test.ts`、`site/src/lib/urlstate.ts`、`site/src/lib/urlstate.test.ts`、`site/src/lib/glyphstore.ts`、`site/src/lib/glyphstore.test.ts`
- Create: `site/src/islands/Catalogue.svelte`、`site/src/islands/FontCard.svelte`、`site/src/islands/FilterPanel.svelte`
- Modify: `site/src/pages/[lang]/index.astro`(挂 `<Catalogue client:load>`,SSR 输出前 24 张卡片静态 HTML 用 preview SVG)
- Create: `site/e2e/catalogue.spec.ts`

**Interfaces:**
- Consumes: C4/C5、`t()`、`withBase`
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

`GlyphStore` 按 C4(chunk LRU=64,in-flight 去重)。

- [x] **Step 1: filters/urlstate 失败测试**(每个筛选维度一用例 + 组合 + 编解码往返恒等 + 未知参数忽略)
- [x] **Step 2: 实现纯函数,vitest 通过**
- [x] **Step 3: glyphstore 失败测试**(mock fetch 计数:同 chunk 并发请求只 fetch 一次;LRU 逐出;`glyphsFor` 覆盖 core 缺口)→ 实现通过
- [x] **Step 4: Svelte 岛屿实现**:FilterPanel(chips/范围/搜索,双语)、FontCard(名称 canvas + 样例 canvas,IntersectionObserver 懒渲染,徽章/chips)、Catalogue(状态↔URL、排序、>60 家族时简单窗口化:仅渲染视口±2 屏)。全局样例输入防抖 150ms。
- [x] **Step 5: e2e**:筛选 form=gothic 后卡片数变化;输入样例文字后某卡片 canvas `toDataURL` 前后不同;缩放 ×2 尺寸翻倍;URL 带 `?forms=gothic` 直开状态恢复;反色切换背景变化。
- [x] **Step 6: 提交** `feat: 目录页筛选与可编辑样例卡片`

### Task 17: 家族详情页(样例编辑器、墨迹示意、元数据)

**Files:**
- Create: `site/src/pages/[lang]/fonts/[slug].astro`(getStaticPaths 遍历 index;SSR 静态输出:头部、元数据侧栏、预渲染 SVG 样例、下载区、墨迹示意 SVG)
- Create: `site/src/islands/SampleEditor.svelte`、`site/src/components/InkDiagram.astro`、`site/src/components/MetaSidebar.astro`、`site/src/components/DownloadList.astro`
- Create: `site/e2e/detail.spec.ts`

**Interfaces:**
- Consumes: C4/C6、GlyphStore、rasterize/paint、`t()`
- Produces: 变体切换事件 `variantchange`(CustomEvent<string>,详情页各岛屿监听);`InkDiagram` props `{bbox, hanInk, claimed}`。

- [x] **Step 1: 失败 e2e**:galmuri fixture 详情页含作者、许可证徽章(auto-high 文案)、每变体 BDF 下载链接(href 含 `dist-downloads` 开发基址)与字节数;样例文本框输入「あ」后 canvas 变化且缺字计数徽标更新;变体切换后度量表数字变化;许可证全文 `<details>` 展开可见。
- [x] **Step 2: 实现静态部分(含墨迹示意:宣称框、汉字墨迹框、max-ink 虚线框三层叠加 SVG + 图例)**
- [x] **Step 3: 实现 SampleEditor(多行、预设句按钮、缩放、反色、网格、缺字高亮开关;fetch 失败显示重试条)**
- [x] **Step 4: e2e 通过** → **Step 5: 提交** `feat: 家族详情页与样例编辑器`

### Task 18: 覆盖率报告 UI、字形网格、查字

**Files:**
- Create: `site/src/islands/CoverageReport.svelte`(分板块折叠、像素方块进度条、变体切换、≤500 缺字展开列表、Unicode 全区段折叠表)
- Create: `site/src/islands/GlyphGrid.svelte`(区段跳转、虚拟滚动、点击检视器弹层:放大位图 canvas + 码位/名称/度量)
- Create: `site/src/lib/intervals.ts` + `intervals.test.ts`(查字数据:格式 = gzip 后的 `u32 familyCount, 每家族: u16 slugLen+utf8, u32 runCount, runCount×(u32 start,u32 end)`;`export class CoverageIndex { static parse(buf): CoverageIndex; covers(slug, text): boolean }`)
- Modify: `pipeline/opf/emit.py`(输出 `coverage-intervals.bin.gz`)+ `pipeline/tests/test_build.py` 追加断言
- Modify: `site/src/islands/Catalogue.svelte`(chars 筛选接入,懒加载 CoverageIndex)
- Create: `site/e2e/coverage.spec.ts`

**Interfaces:**
- Consumes: C6 coverage/unicodeBlocks、C5 variants、GlyphStore
- Produces: `CoverageIndex`(供 filters.ts `charLookup` 注入)。

- [x] **Step 1: intervals 双侧失败测试**(Python 写 → TS parse;`covers("mini","永")===true`、`covers("mini","龘")===false`)→ 实现通过
- [x] **Step 2: 失败 e2e**:详情页 GB/T 2312 行显示 n/3755 与百分比;切变体数字变;缺字≤500 的行可展开且第一个缺字字符正确;字形网格滚动到 CJK 区段渲染出字形,点击出检视器;目录页查字输入「永」后 mini 家族保留、无该字家族消失。
- [x] **Step 3: 实现三岛屿与接线** → **Step 4: e2e 通过** → **Step 5: 提交** `feat: 覆盖率报告、字形网格与查字`

### Task 19: 关于页、404、元信息完备

**Files:**
- Modify: `site/src/pages/[lang]/about.astro`(中文正文:收录标准/度量口径/覆盖率口径方法论——从 spec §4.2/§4.3 改写为面向读者的说明、无 shaping 说明、字表来源致谢表(遍历 charsets 元数据自动生成)、贡献指南含 family.toml 全字段示例、许可证免责声明;英文由子代理翻译)
- Modify: `site/src/pages/404.astro`(馆藏字体 SVG 渲染 404)
- Modify: `site/src/layouts/Base.astro`(og:image/description/canonical per-page)
- Create: `site/e2e/about.spec.ts`

- [x] **Step 1: 失败 e2e**(about 含「墨迹」与致谢表行数 ≥ 字表数;详情页 og:image 指向 `data/og/<slug>.png`;404 含像素渲染)
- [x] **Step 2: 中文正文撰写 → 子代理翻译 → 集成** → **Step 3: e2e 通过** → **Step 4: 提交** `feat: 关于页与元信息`

## Phase C — 导入与全量

### Task 20: 导入工具(zip/BDF/OTB/kbitx)与试点五家族

**Files:**
- Create: `pipeline/opf/ingest/__init__.py`、`manifest.py`(读 `ingest/manifest.toml`)、`extract.py`(zip 解包取 BDF)、`otb.py`(fonttools EBDT/EBLC→Glyph→BDF 写出)、`kbitx.py`(XML→BDF)、`bdfwrite.py`(`write_bdf(f: ParsedFont, out: Path)`)、`run.py`(CLI `python -m opf.ingest.run --manifest … --src … --dest fonts/ [--only slug]`)
- Create: `pipeline/tests/test_ingest.py`(真实文件:galmuri zip 一个、wqy otb、一个 kbitx)
- Create: `ingest/manifest.toml`(先只含试点)+ `docs/import-report.md`(工具生成)

**Interfaces:**
- Produces: manifest 条目模式:

```toml
[[family]]
slug = "baekmuk-batang"
source = "CJK-bitmap-fonts-open-source-2026-08-18/Korean/chocolatemelt--baekmuk"
take = ["batang*.bdf"]            # glob;或 zip = "RELEASE-ASSETS/x.zip", zip_take=["*.bdf"]
license_files = ["COPYRIGHT*"]
name = "Baekmuk Batang"
provenance_url = "https://github.com/chocolatemelt/baekmuk"
convert = ""                       # ""|"otb"|"kbitx"|"ttf"
```

幂等:目标存在且内容 sha 相同 → skip;报告记录 imported/skipped/deduped/todo。

- [x] **Step 1: 失败单测**(zip 抽取重命名、otb→BDF 后 `parse_bdf` 往返字形数一致、kbitx→BDF 同理、`write_bdf` 与 `parse_bdf` 往返恒等、幂等重跑 skip)
- [x] **Step 2: 实现四条路径与报告** → **Step 3: 单测通过**
- [x] **Step 4: 试点导入 5 家族**:ark-pixel(3 尺寸 zip)、galmuri(zip)、baekmuk 四拆之 batang、UnifontEX(单 BDF 12MB 压力)、wqy-bitmapfont(otb 转)。手写试点 manifest 条目 + 每家族 family.toml(form/vibes/homepage 认真填);全量管线跑通,site 构建通过,e2e 全绿;UnifontEX 构建耗时与产物体积记入报告。
- [x] **Step 5: 提交** `feat: 导入工具与试点五家族`(fonts/ 与产报告一并入库)

### Task 21: TTF 栅格化转制

**Files:**
- Create: `pipeline/opf/ingest/rasterize.py`、`pipeline/tests/test_rasterize.py`

**Interfaces:**
- Produces: `detect_native_ppem(ttf: Path) -> int | None`(轮廓格点 GCD:采样 ≤200 字形全部 on-curve 坐标对 em 的公约数,`em/gcd` 为候选;与 name/upem 启发式互校,不一致返回 None);`rasterize_ttf(ttf: Path, ppem: int) -> ParsedFont`(freetype-py `FT_LOAD_TARGET_MONO|FT_LOAD_RENDER`,位图转 Glyph);`verify_sheet(f: ParsedFont, out: Path)`(渲染代表字对照 PNG 供人工抽查)。

- [x] **Step 1: 失败测试**:对收集夹一个已知原生 12px 的像素 TTF(如 fusion-pixel ttf 若在,否则 ChillBitmap)`detect_native_ppem`==标称值;栅格化后「A」墨迹与该家族官方 BDF(如有)一致;无格点规律的普通 TTF(系统 DejaVu 若存在,否则跳过)返回 None。
- [x] **Step 2–4: 失败→实现→通过** → **Step 5: 提交** `feat: TTF 原生格点检测与栅格化`

### Task 22: 全量导入与整理

**Files:**
- Modify: `ingest/manifest.toml`(全收集夹条目;逐目录核查后编写:来源优先级 release-BDF > 仓库 BDF > OTB/kbitx > TTF 转制;PNG/C 头文件家族查重后进 todo)
- Create/Modify: 各 `fonts/<slug>/family.toml`(form 预填建议值 + `# UNVERIFIED` 注释;vibes、homepage、provenance 填实)
- Modify: `docs/import-report.md`(全量报告 + 风格标注待复核清单)

- [x] **Step 1: 分批(Chinese→Japanese→Korean→Pan-CJK→supplement)编写 manifest 并导入,每批:管线全量构建、pytest/vitest/e2e 全绿、抽查 3 家族详情页人工目测,提交一次**(commit `feat: 导入 <批名> 家族`)
- [x] **Step 2: 体积核查**:`site/public/data` 总量与 `dist-downloads` 总量记入报告;若 data >700MB,启用裁剪预案(SMP 稀有块延迟到 Release 托管)并记录
- [x] **Step 3: 全量 e2e + 构建重跑缓存命中率检查;提交** `feat: 全量导入完成与导入报告`

## Phase D — 打磨与上线

### Task 23: 视觉打磨与文案人味

- [x] **Step 1: 加载 frontend-design 技能,按 spec §8 原则全站打磨(排印细节、聚焦态、空态、加载骨架、暗色核对、移动端断点)**;e2e 快照(Playwright screenshot 基线)入库
- [x] **Step 2: 加载 humanizer 技能过一遍全部中文文案;英文文案改动由 Opus/Sonnet 子代理复核**
- [x] **Step 3: 性能预算验证:目录页首屏 JS < 150KB gz(`ls dist` 统计 + Playwright 网络记录);canvas 首绘 < 1s(本地 preview 计时)**
- [x] **Step 4: 提交** `feat: 视觉与文案打磨`

### Task 24: CI 与发布

**Files:**
- Create: `.github/workflows/ci.yml`(PR:py-test + ts-test + astro build)、`.github/workflows/deploy.yml`(main push:管线(缓存 actions/cache 键=fonts 哈希)→ astro build → upload-pages-artifact → deploy-pages;下载物 `gh release upload downloads --clobber` 按 manifest sha 增量)
- Modify: `README.md`(完整使用说明:加字体、family.toml、本地构建、部署)

- [x] **Step 1: 工作流本地静态校验(`act` 不可用则 yaml lint + 逐步核对 action 版本)**
- [x] **Step 2: README 撰写(中文,含英文简版)** → **Step 3: 提交** `chore: CI 工作流与 README`

### Task 25: 最终验证

- [x] **Step 1: 加载 superpowers:verification-before-completion;冷构建全流程计时(<15 分钟目标)、全部测试、体积红线、坏链检查(内链爬取脚本)**
- [x] **Step 2: 对照 spec 逐节走查(§1 成功标准逐条打勾),缺口回填**
- [x] **Step 3: 请求 code-review(/code-review 或 requesting-code-review 技能),修复发现**
- [x] **Step 4: 提交** `chore: 发布前最终验证`

---

## Self-Review 记录

- **Spec 覆盖**:§3 目录约定→T1/T8;§4.1→T2(PCF 解析安排在 T2 后补:见下「补充任务」);§4.2→T3;§4.3→T4/5/6;§4.4→T7;§4.5→T9/10;§4.6→T12;§4.7→T13/24;§4.8→T14/18;§5→T15–19;§6→T20–22;§7→T4/5/6/18;§8→T15/23;§9→T1/24;§10 顺序=Phase A–D;§11 风险→T20 压力/T22 裁剪预案/T21 校验。
- **发现缺口:PCF 解析器无任务** → 增补 Task 2b。
- **类型一致性**:C1–C8 为唯一权威;各任务签名均引用契约,已复查一致(`GlyphChunk.size` 统一为字形数;`InkMetrics.max_ink_cps` 在 C6 emit 时映射为 `maxInkCps`)。

### Task 2b: PCF 解析器(位于 Task 2 之后执行)

**Files:**
- Create: `pipeline/opf/parsers/pcf.py`、`pipeline/tests/test_pcf.py`、fixture:`pipeline/tests/fixtures/mini.pcf`(由 `bdftopcf mini.bdf` 生成并提交)

**Interfaces:**
- Produces: `parse_pcf(path: Path, family_slug: str) -> ParsedFont`(properties/metrics/bitmaps/encoding/glyph-names 表;字节序/位序/scan-unit 处理;编码表 ISO10646 直通,gb2312/jisx0208/ksc5601/big5 经 Python codecs 映射,未知 registry 记警告并丢弃非映射字形)。

- [x] **Step 1: 失败测试**:`parse_pcf(mini.pcf)` 与 `parse_bdf(mini.bdf)` 字形逐字段一致(cp/dwidth/bbw/bbh/rows);压缩 metrics 与非压缩两分支覆盖(fixture 用 `bdftopcf -t` 再生成一份)。
- [x] **Step 2–5: 失败→实现→通过→提交** `feat: PCF 解析器`
