# 免费开源位图（像素）字体 / Free & Open Source Bitmap (Pixel) Fonts

自由许可位图字体的标本馆：把 BDF/PCF 字体放进 `fonts/`，自动构建出一个可检索的
静态目录站——逐字形解析、宣称／墨迹双口径度量、六十余张字表的覆盖率报告、
canvas 像素级样例试写，以及 BDF／PCF／位图 TTF 打包下载。

- 站点：`/zh/`（中文）· `/en/`（English）
- 设计规格：`docs/superpowers/specs/`
- 收录标准、度量与覆盖率口径：见站点「关于」页

## 收录标准

只收录**自由许可**字体，判定从严：授权须明确允许任何人使用、复制、修改、再分发，
**并允许商业使用**；授权须明确适用于本站收录的这份文件，来源链可核验。
仅写「免费」「免费商用」「freeware」或只允许复制的不算；作者尚未落实的
「将来会改成开源许可」也不算。因此站上每一款字体都可放心商用。

复核结论与被排除字体的理由记录在 `docs/import-report.md`。

## 快速开始

需要 Python 3.12+、Node 24+、`bdftopcf`（Debian/Ubuntu：`apt install xfonts-utils`）。

```bash
make setup    # 建 venv、装依赖
make test     # pytest + vitest
make dev      # 构建字体数据并启动开发服务器
make build    # 生产构建（站点在 site/dist/）
make e2e      # Playwright 端到端测试
```

## 添加字体

在 `fonts/` 下建目录，放入 BDF 或 PCF（支持 `.gz`）即被收录：

```text
fonts/my-font/
  my-font-16.bdf
  OFL.txt          # 许可证原文（构建器自动识别常见许可证）
  family.toml      # 可选；不写会生成待补全的 stub，站点标「未整理」
```

`form`（字形分类）与 `vibes`（气质标签）是仅有的建议人工填写项；
授权无法自动识别时，在 `[license]` 块里手填 SPDX、可商用标记与判定依据。

## 批量导入

`ingest/manifest.toml` 描述来源仓库到家族的映射，支持 zip 抽取、OTB／kbitx 转换、
矢量像素 TTF 按原生格点栅格化，以及清单内直接声明 `[family.license]`：

```bash
.venv/bin/python -m fbf.ingest.run \
  --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts \
  --dest fonts --report docs/import-report.md
```

東雲フォント另有专用重建流程（上游以 `.bit` 源码分发）：

```bash
.venv/bin/python -m fbf.ingest.shinonome --repo <shinonome-font 仓库> --dest fonts
```

## 下载格式

每个家族提供三类下载：

- **BDF**（`.bdf.gz`）与 **PCF**（`.pcf.gz`）：逐变体，点阵原始格式
- **位图 TTF**：同一字体（同字重／排布／语言子集）的**全部尺寸**打进一个文件，
  以 EBDT／EBLC strike 承载，`glyf` 内为空轮廓、不含矢量数据；装上即可在支持
  位图 strike 的系统里按尺寸使用
- **家族 ZIP**：全部 BDF ＋ 许可证 ＋ 来源说明

## 搜索

支持简繁互通：搜「东云」能找到「東雲」，反之亦然。异体字等价类在构建期由
Unicode Unihan 的 `kSimplifiedVariant`／`kTraditionalVariant` 生成，
展开后写进索引，前端无需加载映射表。

## 架构

```text
fonts/                字体源（git 版本管理）
pipeline/             Python 管线：解析 → 度量 → 覆盖率 → 许可证 →
                      字形二进制分块 + SVG 预渲染 + 下载物（含 TTF）+ JSON 索引
site/                 Astro 5 静态站点（Svelte 岛屿，canvas 逐像素渲染）
site/public/data/     管线产物（gitignored）
dist-downloads/       下载物 → CI 上传 GitHub Releases
```

部署：GitHub Actions 构建 → GitHub Pages（展示资产）+ Releases 滚动标签
`downloads`（下载物，增量同步）。站点基路径由 `FBF_BASE` 控制，
下载基址由 `FBF_DOWNLOADS_BASE` 控制。

## 许可证

- 本仓库代码：MIT（见 `LICENSE`）
- 各字体：遵循其各自的自由许可（见每个家族目录与详情页）
- 字表与异体字数据：见 `THIRD_PARTY_NOTICES.md`

---

# Free & Open Source Bitmap (Pixel) Fonts (English)

A specimen cabinet for freely-licensed bitmap fonts. Drop BDF/PCF files into
`fonts/` and the build produces a static, searchable catalogue: per-glyph
parsing, nominal-vs-ink metrics, coverage against 60+ character sets, crisp
canvas previews you can type into, and BDF / PCF / bitmap-TTF downloads.

Inclusion is strict: a font is listed only when its license clearly permits
use, copying, modification and redistribution **including commercial use**,
applies to the exact file catalogued here, and comes with a verifiable chain
of provenance.

```bash
make setup && make dev
```
