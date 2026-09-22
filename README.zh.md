# FontPixel.com：开源像素字体馆

[English](README.md) | **简体中文**

自由许可位图字体的标本馆：把 BDF/PCF 字体放进 `fonts/`，自动构建出一个可检索的
静态目录站——逐字形解析、宣称／墨迹双口径度量、六十余张字表的覆盖率报告、
canvas 像素级样例试写，以及 BDF／PCF／位图 TTF 打包下载。

- 站点：<https://fontpixel.com> — `/zh/`（中文）· `/en/`（English）
- 仓库：<https://github.com/fontpixel/fontpixel>
- 文档：[文档索引](docs/README.md) · [评分说明](docs/specs/catalogue-rating.md)
- 收录标准、度量与覆盖率口径：见站点「关于」页

## 收录标准

只收录**自由许可**字体，判定从严：授权须明确允许任何人使用、复制、修改、再分发，
**并允许商业使用**；授权须明确适用于本站收录的这份文件，来源链可核验。
仅写「免费」「免费商用」「freeware」或只允许复制的不算；作者尚未落实的
「将来会改成开源许可」也不算。因此站上每一款字体都可放心商用。

复核结论与被排除字体的理由记录在 `docs/import-report.md`。

## 快速开始

需要 Python 3.12+、Node 24+、Bun 1.4.2、`bdftopcf`（Debian/Ubuntu：`apt install xfonts-utils`）。Bun 管理站点依赖，构建工具仍使用 Node。

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

`forms`（字形分类，可多选）与 `vibes`（气质标签）是仅有的建议人工填写项；
授权无法自动识别时，在 `[license]` 块里手填 SPDX、可商用标记与判定依据。

分类写为数组，例如 `forms = ["gothic", "decorative", "sans"]`。
`gothic`（东亚黑体）自动包含 `sans`，`song`（宋体 / 明朝体）自动包含 `serif`。
首页同时选择多个分类时，匹配任一分类即可；卡片和详情页显示全部分类。
旧的 `form` 单值元数据仍可读取，`mingcho`、`round`、`serif-pixel` 等旧分类及筛选链接
分别归一化为 `song`、`rounded`、`serif`。

`aliases` 收这款字体自己的其它名字——曾用名、上游项目名、字体文件自报的名字、
原生语言名、分词写法不同的同名。只进搜索文本，不在站上显示；中文别名不必写
简繁两份，构建期会自动展开。不收「它所基于的另一款字体」的名字，那类信息写进
`provenance`。

改这些展示字段不会触发字形重算：缓存只认字体文件与 `family.toml` 的结构性
字段（`merge` / `exclude` / `[variants]` / `[license]` / `name` 等），其余改动
走秒级的元数据刷新。真正的重建按 CPU 并行（默认最多 8 进程，`OPF_JOBS` 可调），
单独迭代一个家族用 `--family <slug>`。

## 批量导入

`ingest/manifest.toml` 描述来源仓库到家族的映射，支持 zip 抽取、OTB／kbitx 转换、
矢量像素 TTF 按原生格点栅格化，以及清单内直接声明 `[family.license]`：

```bash
.venv/bin/python -m opf.ingest.run \
  --manifest ingest/manifest.toml \
  --src ../pixel-font-collection-fonts \
  --dest fonts --report docs/import-report.md
```

`--report` 只重写 `docs/import-report.md` 里 `<!-- opf:manual … -->` 标记**之前**的
自动统计部分；标记之后的人工收录记录（逐批收录理由、许可证判定、移除记录）原样保留。
若目标文件存在却没有该标记，导入器会报错拒绝写入，而不是把它覆盖掉。

東雲フォント另有专用重建流程（上游以 `.bit` 源码分发）：

```bash
.venv/bin/python -m opf.ingest.shinonome --repo <shinonome-font 仓库> --dest fonts
```

## 下载格式

每个家族提供三类下载：

- **BDF**（`.bdf.gz`）与 **PCF**（`.pcf.gz`）：逐变体，点阵原始格式
- **位图 TTF**：同一字体（同字重／排布／语言子集）的**全部尺寸**打进一个文件，
  以 EBDT／EBLC strike 承载，`glyf` 内为空轮廓、不含矢量数据；装上即可在支持
  位图 strike 的系统里按尺寸使用
- **矢量 TTF / WOFF2**：构建器生成的方角和圆角像素轮廓版本
- **家族 ZIP**：全部 BDF ＋ 许可证 ＋ 来源说明

## 搜索

支持简繁互通：搜「东云」能找到「東雲」，反之亦然。异体字等价类在构建期由
Unicode Unihan 的 `kSimplifiedVariant`／`kTraditionalVariant` 生成，
展开后写进索引，前端无需加载映射表。

## 架构

```text
fonts/                字体源（git 版本管理）
pipeline/             Python 管线：解析 → 度量 → 覆盖率 → 许可证 →
                      SVG 样张 + BDF/PCF/TTF 等下载物 + JSON 索引
site/                 Astro 5 静态站点（默认 SVG；交互时加载 BDF.gz，Canvas 逐像素渲染）
site/public/data/     管线产物（gitignored）
dist-downloads/       下载物 → 构建时复制到站点 /downloads/
```

部署：GitHub Actions 构建 → 一个 Cloudflare Pages 项目，同时提供页面和
`/downloads/` 字体下载。试字、对比、字形浏览共用下载 BDF.gz，在 Web Worker
中解析并缓存；不发布另一套点阵分片。BDF 导出统一使用 Unicode 编码，保留
点阵、度量及未编码替代字形，`fonts/` 中的上游源文件不变。

`bun run build` 会自动准备下载目录。部署前运行
`python .github/scripts/check_pages_limits.py site/dist`，检查完整产物不超过
20,000 个文件、任一文件不超过 25 MiB。无需第二个 Pages 项目或 R2。
站点基路径由 `OPF_BASE` 控制；`OPF_SITE` 指定规范域名，默认 `https://fontpixel.com`。

首页每页 24 个字体，使用 `/en/page/2/` 等真实静态分页，六种语言共用同一份
默认顺序。默认的 Auto（自动）按固定评分降序排列：主要目标文字的完整度为主，
90 分来自主要文字的完整度，8 分来自该文字的扩展覆盖，其他文字和终端符号
各最多 1 分；跨文字支持不累加，重叠的简繁日汉字不重复加分。
8–16px 以外的原生尺寸逐渐小幅降权。许可另作小幅修正：GPL 带字体例外
降 1.5%，普通 GPL 降 4%，CC BY-SA 降 2%；OFL 与宽松许可保持基准，
双许可证按 OR 可选择、AND 同时适用的关系计算。
另按站主的审美偏好，对指定家族加 0.5、1 或 1.5 分；配置集中在
`site/src/lib/rating-adjustments.ts`，最终排序分可以超过 100，避免加分被截掉。
Google Fonts 名单中的家族另加 1 分，名单集中在 `site/src/lib/google-fonts.ts`。
CJK 使用常用字表及更宽松的覆盖曲线，不要求覆盖全部 Unicode。
同分按家族 slug 排序；刷新、切换语言和重新构建都不会随机重排。
具体口径见[评分说明](docs/specs/catalogue-rating.md)。
筛选保留相对顺序并回到第一页；名称、尺寸和字形数排序仍可选择。
每页直接输出字体链接、SVG 和分页链接，无 JavaScript 也可翻阅完整目录。

默认预览先在 8–16px（含两端）中选择字形最多的变体；没有该范围的尺寸时，
再从所有尺寸中选择字形最多者。`family.toml` 的 `default_variant` 可显式指定。
字号相同或字形数量相同不会引入随机选择；完整构建与缓存刷新使用同一规则。

## SEO、无障碍与质量检查

静态构建生成 `robots.txt`、多语言 sitemap、`llms.txt`、文档 Markdown 版本和
默认分享图。页面共用 canonical、语言版本链接、Open Graph、Twitter 卡片及结构化数据；
字体详情页使用对应字体的样张图片。

```bash
cd site
bun run check              # Astro、TypeScript 和 Svelte 检查
bun run build              # 质量审计前先生成生产构建
bun run audit:seo          # 检查所有生成页面和 sitemap 条目
bun run test:a11y          # axe 无障碍检查与键盘操作回归测试
bun run audit:lighthouse   # 移动端与桌面端 Lighthouse 报告
```

Lighthouse 报告保存在 `site/quality-reports/`。代表页面各测三次冷缓存，性能分数中位数要求至少 90，
每次的无障碍、最佳实践和 SEO 均要求 100。自动检查与键盘测试相互补充，不能替代辅助技术实测。

本次检查范围与结果见 [2026-09-22 质量报告](docs/audits/site-quality-2026-09-22.md)。

## 许可证

- 本仓库代码：MIT（见 `LICENSE`）
- 各字体：遵循其各自的自由许可（见每个家族目录与详情页）
- 字表与异体字数据：见 `THIRD_PARTY_NOTICES.md`
