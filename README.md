# 点阵字库 Pixel Font Collection

开源点阵字体的标本馆:把 BDF/PCF 字体放进 `fonts/`,自动构建出一个可检索的
静态目录站——逐字形解析、宣称/墨迹双口径度量、六十余张字表的覆盖率报告、
canvas 像素级样例试写,以及 BDF/PCF 打包下载。

- 站点(中文):`/zh/` · English:`/en/`
- 设计规格:`docs/superpowers/specs/2026-08-21-pixel-font-collection-design.md`
- 覆盖率与度量口径:见站点「关于」页

## 快速开始

需要 Python 3.12+、Node 24+、`bdftopcf`(Debian/Ubuntu:`apt install xfonts-utils`)。

```bash
make setup    # 建 venv、装依赖
make test     # pytest + vitest
make dev      # 构建字体数据并启动开发服务器
make build    # 生产构建(站点在 site/dist/)
make e2e      # Playwright 端到端测试
```

## 添加字体

在 `fonts/` 下建一个目录,放入 BDF 或 PCF(支持 `.gz`),即被收录:

```text
fonts/my-font/
  my-font-16.bdf
  OFL.txt          # 许可证原文(构建器自动识别常见许可证)
  family.toml      # 可选;不写会生成待补全的 stub,站点标「未整理」
```

`family.toml` 完整字段见站点「关于 → 添加字体」或
`pipeline/pfc/familymeta.py`;`form`(字形分类)与 `vibes`(气质标签)
是仅有的建议人工填写项。

## 批量导入(收集夹 → fonts/)

`ingest/manifest.toml` 描述来源仓库到家族的映射(zip 抽取、OTB/kbitx 转换、
矢量像素 TTF 按原生格点栅格化):

```bash
.venv/bin/python -m pfc.ingest.run \
  --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts \
  --dest fonts --report docs/import-report.md
```

幂等可重跑;报告列出导入/跳过/待议清单。

## 架构

```text
fonts/                字体源(git 版本管理)
pipeline/             Python 管线:解析 → 度量 → 覆盖率 → 许可证 →
                      字形二进制分块 + SVG 预渲染 + 下载物 + JSON 索引
site/                 Astro 5 静态站点(Svelte 岛屿,canvas 逐像素渲染)
site/public/data/     管线产物(gitignored,~15MB/5 家族)
dist-downloads/       BDF/PCF/zip 下载物 → CI 上传 GitHub Releases
```

部署:GitHub Actions 构建 → GitHub Pages(展示资产)+
Releases 滚动标签 `downloads`(下载物,增量同步)。
站点基路径由 `PFC_BASE` 控制(默认 `/pixel-font-collection`),
下载基址由 `PFC_DOWNLOADS_BASE` 控制(本地退回 `/downloads`)。

## 许可证

- 本仓库代码:MIT(见 `LICENSE`)
- 各字体:遵循其各自的许可证(见每个家族目录与详情页)
- 字表数据:见 `THIRD_PARTY_NOTICES.md`

---

# Pixel Font Collection (English)

A specimen cabinet for open-source bitmap fonts. Drop BDF/PCF files into
`fonts/` and the build produces a static, searchable catalogue: per-glyph
parsing, nominal-vs-ink metrics, coverage reports against 60+ character
sets, crisp canvas previews you can type into, and BDF/PCF downloads.

```bash
make setup && make dev
```

See the About page on the site for methodology; `ingest/manifest.toml`
drives bulk imports from the collection folder. Site code is MIT; each
font keeps its own license; character-set data credits are in
`THIRD_PARTY_NOTICES.md`.
