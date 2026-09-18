# Hosting capacity audit — 2026-09-17

> 本文保留迁移当日的容量、验证结果与设计。下文的随机排序已被
> [固定 Auto 评分](../specs/catalogue-rating.md) 替代；当前构建与部署命令见
> [项目 README](../../README.md)。数量和平台限制是当日记录。

已完成 SVG 固定样张 + 下载 BDF.gz 复用，以及每页 24 个字体的静态分页。包含全部 411 个字体家族、1,433 个变体和所有格式下载的完整站点，可放入**一个免费 Cloudflare Pages 项目**。当前不需要第二个下载项目或 R2。

本次已修改构建和部署配置并完成本地验证，未执行线上部署、修改 Cloudflare 账户或域名。

## 最终生产构建实测

按发布目录 `site/dist/` 中的文件路径计数，字节数为实际文件长度，不按传输压缩率或内容去重估算。MiB = 2^20 bytes，GiB = 2^30 bytes。统计保守包含 `_headers` 等控制文件。

| 范围 | 文件数 | 字节数 | 大小 |
| --- | ---: | ---: | ---: |
| 主站，排除 downloads/ | 5,233 | 2,074,873,684 | 1.93 GiB |
| downloads/，含 manifest | 5,892 | 2,106,619,941 | 1.96 GiB |
| 完整发布目录 | **11,125** | **4,181,493,625** | **3.89 GiB** |
| 主站中的 data/ | 2,538 | 66,625,830 | 63.54 MiB |

最大文件仍是 `downloads/taipei-pixel-24px-round.ttf`，22,187,372 bytes（21.16 MiB）。没有文件超过 25 MiB；相对 20,000 个文件的上限，还余 **8,875 个文件**。最大主站文件为文档演示用 `bdfparser_fonts/unifont-13.0.04.bdf`，9,331,390 bytes（8.90 MiB）。

此前清理残留文件后的完整站点加下载为 24,584 个文件；本次删除 14,442 个有效旧预览分片及 manifest，同时增加固定标题/卡片 SVG、102 个分页页面和新的前端资源，最终净减少 13,459 个文件。发布目录中已不存在 `data/packs/`。

## 渲染与字体数据

目录现在为每种语言 18 页，共 108 个目录页。每次 Astro 构建生成一个新 seed，
以轻度加权随机排列全部字体；六种语言共用这一顺序。排序固定在发布产物中，
不按日期变化、不在网址中添加 seed，重新上传同一产物也不会改变顺序。
两次独立构建已验证顺序不同；每次构建内全部 411 个家族恰好出现一次，
各分页均有自身的 canonical 和 sitemap 条目。关闭 JavaScript 仍可查看样张和翻页。

随机权重为 1–1.5：完整 CJK 书写系统覆盖加 0.25，字符数量按对数增加、
最多加 0.25。筛选保持相对顺序，筛选或排序改变时回到第一页；
分页链接保留筛选条件，翻页保留自定义试字和缩放。

- 首页默认卡片的字体标题、固定样句使用预生成 SVG。进入首页不需要下载整套 BDF；输入自定义文字后，才为可见卡片加载对应变体。
- 详情页顶部继续使用 SVG。交互试字、字号/地区变体切换、对比、字形浏览直接读取 `/downloads/{family}--{variant}.bdf.gz`，与下载按钮指向同一份字体文件。
- BDF 在 Web Worker 中解压和解析，Canvas 继续按原生点阵绘图。各组件共用加载器，合并并发请求，并缓存最近使用的 8 个变体。
- 字形浏览的范围和字形表由 BDF 在浏览器内生成，不再发布第二份完整字库。PNG、点阵文本和 BDF 字形复制功能保留；字体尚未加载完成时复制按钮禁用。
- 原有默认样句及地区变体匹配逻辑保留，默认样句不跟随网页语言切换。

部分旧 BDF 使用 GB2312、JIS 等编码。现在下载 BDF 统一标记为 Unicode，编码来自管线已解析的 Unicode 码点；保留点阵、advance、bbox、ascent/descent、原生字号和未编码字形。家族 ZIP 内的 BDF 同步更新。`fonts/` 中上游源文件不因本次迁移而修改。

首次自由试字需要读取所选变体的完整 BDF.gz，这是取消按字符分片的实际取舍。固定 SVG 避免了默认目录页的整字体请求；Worker 解析与缓存避免在主线程反复解析。保留现有 WOFF2 下载，但它不再需要承担与全部原生 BDF 变体一一对应的预览职责。

## 内容与功能验证

- 迁移前后逐变体比较 1,433 个变体：6,988,676 个已编码字形、8,903 个未编码字形。对码点、advance、bbox、完整位图字节计算 SHA-256，同时比较字号、ascent/descent，全部一致。
- 全部 5,891 个下载文件及其发布副本的 SHA-256 与下载 manifest 一致。全部 1,433 个 ZIP 内 BDF 与单独下载的 BDF 解压后逐字节相同。
- Python：229 项测试通过。Vitest：77 项测试通过。此前预览迁移和分页的 Playwright 回归覆盖 158 项；本次多分类更新针对分类、目录、详情、分页和响应式布局的 87 项回归全部通过。Astro/Svelte 类型检查：0 错误，保留 18 个已有 Svelte 警告。
- Astro 生产构建成功，生成 2,630 个页面。Pages 容量检查通过；容量检查器的空目录、文件数和单文件大小边界也已验证。
- 浏览器已验证默认卡片零 BDF 请求、编辑后加载同一下载文件、试字与字形浏览共享请求、CJK 地区变体、点阵复制、对比和多语言默认样句。另实测 UnifontEX 的 65,436 字符变体正常加载、渲染。

## 部署方式

[deploy.yml](../../.github/workflows/deploy.yml) 已改为 GitHub Actions 构建后，通过 Wrangler 把完整 `site/dist/` 上传到同一个 Pages 项目。已取消该流程中的 R2 同步步骤。现有 Cloudflare API token、account ID 和项目名仍由仓库 secrets/variables 提供。

`npm run dev` 和 `npm run build` 会先把下载清单中的文件同步到 `site/public/downloads/`。生产 `_headers` 为下载设置附件和 gzip MIME 类型。Pages 提供普通静态文件，不使用 Functions。

CI 与正式部署都会在上传前运行：

```bash
python .github/scripts/check_pages_limits.py site/dist
```

检查覆盖整个发布目录，包括所有字体下载。未来继续增加字体时，超过 20,000 个文件或任何文件超过 25 MiB 会直接阻止部署。原有 `--budget-mb 900` 仅检查展示数据，不代替这项完整产物检查。

## 当前官方限制

- 免费 Pages 每站最多 20,000 个文件、单文件最多 25 MiB；官方没有另列类似 GitHub Pages 的 1 GB 站点总量上限。当前 3.89 GiB 完整目录符合已列出的文件限制。[Pages limits](https://developers.cloudflare.com/pages/platform/limits/)
- 静态资源请求在免费和付费计划中都免费且不限次数；Functions 请求另计，本方案不使用 Functions。[Static asset requests](https://developers.cloudflare.com/pages/functions/pricing/)
- 应使用 Wrangler/CI 上传。控制台拖放上传只有 1,000 文件上限，不能用于这个完整目录。[Direct Upload limits](https://developers.cloudflare.com/pages/get-started/direct-upload/)
- Cloudflare 托管构建有每月 500 次、单次 20 分钟限制。本仓库在 GitHub Actions 构建再上传，不依赖 Pages 托管构建来运行字体转换。[Build limits](https://developers.cloudflare.com/pages/platform/limits/)
- GitHub Pages 的发布站点上限为 1 GB；当前主站即使不含下载仍超出，所以本次改造并没有使 GitHub Pages 变得适用。[GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)

以上结论基于当前完整本地产物与官方公开限制，不代表已进行线上部署或检查账户配置。
