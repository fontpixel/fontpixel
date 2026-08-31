# 开源像素字体馆 — 设计规格

日期:2026-08-21
状态:已与项目所有者逐节确认通过
站名:开源像素字体馆 / Open Pixel Fonts
部署:GitHub Pages(展示资产)+ GitHub Releases(下载物)

## 1. 背景与目标

把收集来的开源点阵字体(以 CJK 为主)整理成一个自动构建的静态目录网站。字体源以 BDF/PCF 放进 `fonts/` 目录即自动收录。旧项目 `../open-pixel-fonts-old` 整体废弃重做;其覆盖率思路保留并大幅扩展,视觉、交互、工程全部重来。旧项目确认的三大败因:视觉有 AI 味、交互与功能不足、工程质量差(含 hash 路由不利分享)。

**成功标准**

- 全部导入家族可重复构建,构建产物齐全(字形包、预渲染、下载物、索引)。
- 站点 Pages 体积 ≤ 900MB(CI 硬检查);目录页首屏 JS < 150KB gz。
- 每个字体家族:属性齐全、覆盖率报告完整、样例可编辑、BDF/PCF 可下载。
- 视觉经得起挑剔:不像模板、不像 AI 产物。
- 中英双语完整可用。

**收录标准(2026-08-29 收紧)**

只收录自由许可字体:授权须明确允许使用、复制、修改、再分发**并允许商业使用**,
须明确适用于收录的这份文件,来源链可核验。仅标「免费」「免费商用」「freeware」
或只允许复制的不算;作者尚未落实的「将来改开源许可」也不算。

**非目标(v1 不做)**

- 后端、账号、评论、用户上传。
- OTF/WOFF2 下载分发(转制来源的原始矢量字体给上游链接,不再分发)。
  注:位图 TTF 已于 2026-08-29 加入,见 §4.7——它承载的是点阵 strike、不含矢量轮廓,与此处排除的矢量分发不是一回事。
- 彩色字体、emoji、竖排样例。

## 2. 已确认的关键决策

| 决策点 | 结论 |
|---|---|
| 导入范围 | 原生点阵格式(BDF、zip 内 BDF、OTB、kbitx、FNT 视情况)直接收;矢量化像素 TTF/OTF/woff2 栅格化转制为 BDF 并标注;PNG 图源/C 头文件逐个评估,冗余即跳过 |
| 部署 | GitHub Pages;下载物走 GitHub Releases 滚动发布 |
| 语言 | 中英双语,`/zh/`(默认)与 `/en/` 双路由 |
| 目录单位 | 真实字体家族(导入时拆分,如 baekmuk 拆成 4 个家族) |
| 源策略 | `fonts/` 源(BDF+元数据+许可证)进主仓库 git;生成物不进 git |
| 风格体系 | 双层:受控「字形分类」+ 自由「气质标签」,均可筛选 |
| 站点架构 | Astro 5 SSG + Svelte 5 岛屿 + TypeScript |
| 样例渲染 | Canvas 点阵直绘(字形二进制分块)+ 构建期 SVG 预渲染保 SEO/无 JS |
| 构建管线 | Python 3.12(fonttools、freetype-py),pytest 覆盖 |

## 3. 仓库与目录约定

```
open-pixel-fonts/
├── fonts/                        # 字体源,git 追踪
│   └── <family-slug>/
│       ├── family.toml           # 手填元数据(可缺省,构建器生成 stub)
│       ├── LICENSE / OFL.txt …   # 上游许可证原文
│       └── *.bdf | *.bdf.gz | *.pcf | *.pcf.gz   # 每文件=一个变体
├── pipeline/                     # Python 构建管线
│   ├── build.py                  # 入口:fonts/ → 产物
│   ├── parsers/                  # bdf.py pcf.py otb.py kbitx.py
│   ├── coverage/                 # 覆盖率计算 + data/ 字表(版本化,含来源说明)
│   ├── metrics.py                # 宣称/墨迹度量
│   ├── licenses.py               # 许可证识别
│   ├── glyphpack.py              # 字形包写入器
│   ├── prerender.py              # SVG 样例 + og:image PNG
│   ├── downloads.py              # bdf.gz / pcf.gz / 家族 zip + manifest
│   └── ingest/                   # 导入工具(见 §6)
├── site/                         # Astro 项目
│   ├── src/pages/                # 路由(含 [lang])
│   ├── src/islands/              # Svelte 岛屿
│   ├── src/lib/                  # 字形包解码器、GlyphStore、筛选逻辑(vitest)
│   └── public/data/              # 管线产物(gitignored)
├── dist-downloads/               # 下载物(gitignored,CI 上传 Releases)
├── docs/superpowers/specs/       # 设计与计划文档
└── .github/workflows/build.yml
```

### 3.1 family.toml

只填机器推不出的字段;缺省时构建器自动生成带 TODO 注释的 stub 并在站点标「未整理」。

```toml
name = "Galmuri"                  # 必填(stub 从目录名生成)
name_zh = ""                      # 可选,中文显示名
author = "quiple"
homepage = "https://galmuri.quiple.dev"
repository = "https://github.com/quiple/galmuri"
description = ""                  # 可选,一句话介绍(中文;英文由翻译流程生成)
form = "gothic"                   # 受控字形分类,见 §3.3;未填=「未分类」
vibes = ["retro-game"]            # 自由气质标签(kebab-case,站点汇总为筛选项)
converted_from = ""               # 转制来源:"ttf"|"otf"|"woff2"|留空=原生
provenance = ""                   # 来源与获取说明(导入工具自动写入)

[license]                         # 自动识别成功时整块省略
spdx = "OFL-1.1"                  # 或 LicenseRef-<name>
name = ""                         # 自定义许可证显示名
file = "OFL.txt"                  # 指向目录内文本
note = ""                         # 附加限制说明

[samples]                         # 可选,覆盖默认样例句
zh-Hans = "…"

[variants."Galmuri11.bdf"]        # 可选,逐变体覆写
display = "Galmuri 11"
weight = "regular"                # regular|bold|light|…
spacing = "proportional"          # monospaced|proportional
script_subset = ""                # zh-Hans|zh-Hant|ja|ko|latin|…(fusion-pixel 式分包)
```

### 3.2 变体模型

变体维度 = 宣称尺寸 × 粗细 × 等宽/比例 × 语言子集。自动解析优先级:BDF/PCF 属性(`PIXEL_SIZE`、`WEIGHT_NAME`、`SPACING`、`CHARSET_REGISTRY` 等)→ 文件名启发式 → `[variants]` 手工覆写。家族页按「尺寸为主轴、其余为切换器」组织变体。

### 3.3 受控字形分类(form)

`gothic` 黑体/ゴシック、`mingcho` 宋体/明朝、`rounded` 圆体、`kai` 楷体、`fangsong` 仿宋、`songti-serif` 衬线像素(西文 serif 系)、`sans` 无衬线像素(西文)、`script` 手写、`decorative` 装饰/美术、`terminal` 终端/系统、`other` 其他。词表在实现时可增删,但保持受控(站点筛选器逐项列出,双语名)。一个家族一个主分类,允许最多一个副分类。

## 4. 构建管线

流程:扫描 → 解析 → 度量 → 覆盖率 → 许可证 → 产物(字形包/预渲染/下载物/索引)。全程按「文件内容哈希 + 管线版本号」增量缓存(`.cache/`,gitignored)。

### 4.1 解析器

- **BDF**:完整属性表、逐字形 `ENCODING`(≥0 者入编码表)、`BBX`、`DWIDTH`、位图。容忍常见方言(重复属性、非标准行)并记录构建警告。
- **PCF**:properties、metrics、ink metrics、bitmaps、encoding、glyph names 各表,处理字节序/位序/扫描单元。非 Unicode 编码(ISO 8859、GB2312、JIS、KS、Big5 等)映射到 Unicode;无法可靠映射的记警告并在站点展示。
- **OTB**:fonttools 读 `EBDT/EBLC`(导入期转为 BDF 落盘,站点管线只消费 BDF/PCF)。
- **kbitx / FNT**:同上,仅导入期使用。

### 4.2 度量口径(站点公示于「关于」页)

- **宣称大小**:`PIXEL_SIZE` → `SIZE`(pt@dpi 换算)→ `FONTBOUNDINGBOX` 高度,取整像素。
- **汉字墨迹字面**:取该字体已覆盖的通用规范一级字表交集(不足 100 字时退化为全部 CJK 统一表意字形),逐字形算实际点亮像素外接框,宽、高分别取中位数,报「W×H」。无汉字的字体改报:大写 A–Z 墨迹高中位数(cap height)、小写 x 高、ASCII 最大墨迹框。
- **全字体最大墨迹**:全部字形最大墨迹宽/高,并记录达到极值的字形码位(组合符、超宽 PUA 字形会使其大于宣称框,属正常,页面加脚注)。
- 另采集:ascent/descent、`FONTBOUNDINGBOX`、DWIDTH 分布(等宽判定:≥99% 字形同宽即视为等宽,与 `SPACING` 属性互校)。

### 4.3 覆盖率计算

编码表中的码位集合(bitset)对照 §7 各字表逐一统计。计数规则:一码位一计;分母为版本化数据文件中的码位数;兼容表意字与统一表意字分列,FA0E/FA0F/FA11/FA13/FA14/FA1F/FA21/FA23/FA24/FA27/FA28/FA29 十二个「实为统一字」单独脚注。覆盖率按变体计算;家族级筛选取「任一变体达标」。

### 4.4 许可证识别

三级置信:

1. **auto-高**:目录内 `LICENSE*`、`LICENCE*`、`COPYING*`、`OFL*` 及扫描到的许可证文本,归一化空白后与已知全文指纹匹配。首批指纹:OFL-1.1、OFL-1.0、MIT、Apache-2.0、GPL-2.0/3.0(含 Font Exception 变体)、LGPL-2.1、CC0-1.0、CC-BY-4.0、CC-BY-SA-4.0、WTFPL、Unlicense、IPA Font License 1.0、M+ Font License(旧版)、Baekmuk License、公有领域声明。
2. **auto-低**:仅从 BDF `COPYRIGHT`/`NOTICE` 属性得到提示,站点显示「待确认」。
3. **manual**:`family.toml` `[license]` 覆写一切。

未识别 → 构建警告 + 站点「许可证未确认」警示条。（原有的 `commercial` 字段已于 2026-08-31 移除:收录标准本身就要求授权允许商用,站上不存在不可商用的字体,逐字体再记一个恒为真的字段是冗余,也曾因白名单不全而误报「未知」。）站点全站脚注:许可证信息仅供参考,以上游原文为准。

### 4.5 字形包(canvas 渲染数据源)

- 每变体一份 manifest JSON(区间 → 分块文件、字节数、字形数、sha256)+ 若干二进制分块,分块以 gzip 存储(`.bin.gz`),前端 `DecompressionStream('gzip')` 解压。
- 分块按码位区间划分,目标单块 gzip 后 ≤ 16KB,支持按码位随机访问(块内索引:码位 → 度量 + 位图偏移;度量含 DWIDTH、BBX 四元组)。
- 每变体额外一个**核心包**:可打印 ASCII + 平/片假名 + 谚文兼容字母 + 全部默认样例句用字 + 家族显示名用字,目标 ≤ 8KB gz;目录卡片(名称+样例行)仅凭核心包即可渲染,编辑样例才触发分块拉取。
- 精确二进制布局(魔数、版本、字段宽度)在实现阶段随解码器测试一起定,规格要求:v1 版本号内向后兼容,解码为纯 TS 无依赖。

### 4.6 预渲染与社交卡片

- 每家族默认样例构建期渲染为内联 SVG(横向连续像素合并为 rect,控制节点数),写入静态 HTML:无 JS 可见、SEO 可索引;JS 就绪后无缝替换为可编辑 canvas。
- 每家族 og:image PNG(Pillow 绘制,含站名与家族名样例)。

### 4.7 下载物与 Releases

- 每变体:`<family>--<file>.bdf.gz`、`<family>--<file>.pcf.gz`(bdftopcf 生成;转换失败记警告并只提供 BDF)。每家族:`<family>.zip`(全部变体 BDF + 许可证 + 来源说明 README)。
- **位图 TTF**(2026-08-29 新增):按(字重 × 排布 × 语言子集)分组,同组的全部像素尺寸打进一个 TTF,以 EBDT/EBLC strike 承载,`glyf` 内为空轮廓、不含矢量数据。文件名只带组间真正有差异的维度(单组家族即 `<family>.ttf`)。实现见 `pipeline/opf/ttfexport.py`,以「构建 → 用 OTB 解析器读回 → 与源 BDF 逐字节比对」验证。
- CI 上传到滚动 Release(tag `downloads`),按 manifest sha256 只替换有变化的资产;站点链接指向 `releases/download/downloads/<asset>`,并显示文件大小与 sha256。
- 本地 dev:链接指向本地 `dist-downloads/`(dev 服务器静态挂载);生产由环境变量切换基址。

### 4.8 索引产物

- `index.json`(目录页,目标 ≤ 50KB gz):每家族 slug、双语名、form/vibes、尺寸列表、粗细、等宽性、书写系统、许可证(spdx)、关键覆盖摘要、汉字墨迹与宣称尺寸、字形数、作者、是否转制、核心包与预渲染路径、变体清单。
- 每家族 `detail.json`:完整覆盖率树(逐变体)、全部度量、构建警告、下载 manifest。
- `coverage-intervals.bin.gz`:全部家族的覆盖码位区间(家族级并集),查字功能与缺字高亮按需加载一次。

## 5. 站点信息架构

路由(`ASTRO_BASE` 可配,默认 `/open-pixel-fonts`):

- `/` — 按 `navigator.language` 跳转 zh/en 的极小页,带 hreflang。
- `/zh/`、`/en/` — 目录页(即首页)。
- `/{lang}/fonts/<slug>/` — 家族详情页。
- `/{lang}/about/` — 关于:收录标准、度量与覆盖率口径方法论、字表来源与致谢、贡献指南(如何添加字体/写 family.toml)、许可证免责声明。
- `/404.html` — 用馆藏字体渲染的 404。

### 5.1 目录页

- 工具栏:全文搜索(名称/作者/标签;**简繁互通**——搜「东云」命中「東雲」,异体字等价类由 Unihan `kSimplifiedVariant`/`kTraditionalVariant` 在构建期展开进 `searchText`,前端无需映射表)、**全局样例文本框**(即改即绘,应用到全部卡片)、像素缩放 ×1/×2/×3、反色(白底黑字/黑底白字)。
- 筛选器(全部序列化进 URL query,可分享):字形分类、气质标签、宣称尺寸(离散 px chips)、汉字墨迹高(范围)、书写系统、许可证(SPDX 多选;「仅看可商用」开关已于 2026-08-29 移除——收录标准已收紧为严格自由许可,全部字体均可商用,该筛选器不再有意义)、等宽/比例、粗细、原生/转制、覆盖率达标预设(GB2312≥99%、常用国字≥99%、JIS 第 1 水準≥99%、假名 100%、KS X 1001 谚文≥99%,以及「任选字表+阈值」自定义)、**查字**(输入任意字符,只显示全覆盖的家族)。
- 排序:名称/宣称尺寸/字形数/最近加入。
- 卡片:家族名用该字体自渲染 + 样例行 canvas(跟随全局样例,懒加载 IntersectionObserver)+ 元数据 chips(尺寸、分类、许可证、书写系统、字形数、转制徽章、未整理徽章)。样例中该字体缺的字以占位框+高亮提示。
- 家族数超过视口承载时虚拟滚动(实现期视实测决定,预计 ~100+ 家族需要)。

### 5.2 家族详情页

- 头部:家族名大号自渲染、作者/主页/仓库/来源、许可证徽章(置信级可见,全文折叠展开)、form/vibes、转制说明(如适用)。
- 变体切换:尺寸主轴 + 粗细/等宽/语言子集切换器。
- **可编辑样例**:多行输入、分文种预设句、缩放、反色、网格线开关、**缺字高亮**开关。默认句:zh-Hans「天地玄黄,宇宙洪荒。日月盈昃,辰宿列张。」;zh-Hant「落霞與孤鶩齊飛,秋水共長天一色。」;ja「色は匂へど 散りぬるを 我が世誰ぞ 常ならむ」;ko「다람쥐 헌 쳇바퀴에 타고파」;latin「Sphinx of black quartz, judge my vow. 0123456789」。家族默认取其主书写系统的句子,`[samples]` 可覆写。
- **宣称 vs 墨迹可视化**:小型示意图,宣称框与代表汉字墨迹框叠加,数字标注。
- **字形网格浏览器**:按 Unicode 区段跳转的虚拟滚动网格,点击字形 → 检视器(放大位图、码位、字形名、BBX/DWIDTH/墨迹框)。数据按滚动位置懒取分块。
- **覆盖率报告**:§7 八大板块,进度条为离散像素方块;逐变体切换;每行:名称(双语)、n/分母、百分比、来源 tooltip;缺字数 ≤ 500 的行可展开查看缺字列表(以文本呈现,可复制)。
- 下载区:逐变体 BDF/PCF(标大小与 sha256)+ 家族 zip;转制家族附上游矢量字体链接。
- 度量区:全部 §4.2 采集值表格。

### 5.3 客户端数据流

单例 GlyphStore(TS):manifest 缓存 + 分块 LRU + 按需 fetch;目录页与详情页共用。筛选逻辑纯函数化(vitest 覆盖)。查字触发时才加载 `coverage-intervals.bin.gz`。

## 6. 导入工具(pipeline/ingest)

一次性批量 + 未来增量均可用。输入 `../pixel-font-collection-fonts/`,输出 `fonts/` 家族目录 + 导入报告。

- **映射清单** `ingest/manifest.toml`(人工维护,代码辅助生成初稿):源路径 → 目标家族(含拆分,如 `chocolatemelt--baekmuk` → `baekmuk-batang`/`baekmuk-dotum`/`baekmuk-gulim`/`baekmuk-hline`;`RELEASE-ASSETS/*.zip` → 解包取 BDF)。
- **来源优先级**:官方 release BDF > 仓库内 BDF > OTB/kbitx 转换 > TTF 栅格化。同一字体多处出现时取最高优先级,重复项记入报告。
- **TTF/OTF/woff2 转制**:freetype-py 以原生格点 ppem 栅格化(单色模式)。原生 ppem 判定:轮廓坐标格点 GCD / em 整除关系 + 元数据,并渲染代表字对照校验;判定失败的家族进报告人工处理。转制家族写 `converted_from` 与 `provenance`。
- **许可证与出处**:从源目录复制许可证文本;`provenance` 记录源 URL、获取日期、转换方式。
- **跳过策略**:PNG 图源、C 头文件、u8g2 二进制等,若同字体已有其他可用来源则跳过;确无来源的列入报告的「待议」清单,逐个决定。
- **幂等**:重跑不产生重复;目标目录已存在且哈希一致则跳过。
- **报告** `docs/import-report.md`:收录清单、拆分决定、去重记录、跳过与原因、待人工事项(含风格标注待办清单,预填建议值并标「未复核」)。

## 7. 覆盖率体系(八大板块)

每字表:双语名称、来源与版本、一句话用途说明(tooltip)、分母取自 `pipeline/coverage/data/` 版本化数据文件(每个文件头部注明来源、版本、获取日期、许可)。旧项目 `scripts/data/cjk-tables/` 的数据(源自 CJK-character-count,MIT)迁移复用并按下表补齐;第三方数据在 `THIRD_PARTY_NOTICES.md` 致谢。

1. **总览**:总编码字符(分母 Unicode 17.0 已分配)、按平面分布(BMP/SMP/SIP/TIP/SSP)、PUA 三区(BMP PUA / Plane 15 / Plane 16)、汉字总数(URO+扩展 A–J)、兼容表意字(含补充区,附 12 字脚注)。
2. **简体·国家标准**:GB/T 2312-1980(一级 3755 / 二级 3008 分列)、GB/T 12345-1990、GBK 汉字、GB 18030-2022 实现级别 1 / 2 / 3。
3. **简体·语文规范**:通用规范汉字表 2013(一级 3500 / 二级 3000 / 三级 1605 分列)、现代汉语常用字表(常用 2500 / 次常用 1000)、现代汉语通用字表 7000、义务教育语文课程常用字表 3500、古籍印刷通用字规范字形表、康熙部首 214、CJK 部首补充 115;末尾附厂商口径:汉仪简繁字表、方正简繁字表。
4. **繁体·台湾**:常用国字标准字体表 4808、次常用国字标准字体表 6343、Big5(常用 5401 / 次常用分列)、注音符号(含扩展)。
5. **繁体·香港**:常用字字形表 4825、HKSCS-2016。
6. **日文**:JIS X 0208(非汉字 / 第 1 水準 2965 / 第 2 水準 3390 分列)、JIS X 0213 第 3 / 第 4 水準、常用漢字表 2136、教育漢字 1026、人名用漢字、平假名、片假名、半角假名、JIS X 0201。
7. **韩文**:KS X 1001(谚文音节 2350 / 汉字 4888 / 符号)、现代谚文全 11172、谚文兼容字母、谚文字母(Jamo)。
8. **泛用与国际**:IICore 9810、UnihanCore2020、CJK 统一表意扩展 A–J 逐区、WGL4 652、Latin(Basic/1 Supplement/Extended-A/B)、希腊与科普特、西里尔(基本+扩展)、越南语拉丁字符集、CP437、制表符 Box Drawing、方块元素 Block Elements、Powerline 符号(U+E0A0–E0D4)、盲文、以及**全部 Unicode 17.0 区段**可折叠总表(默认只显示非零区段)。

目录卡片按书写系统自动挑选达标徽章(如 GB2312✓、Big5✓、JIS1✓、KS X 1001✓、假名✓)。

## 8. 视觉方向

概念:**标本馆** — 字体是展品,界面是玻璃展柜。

- 近单色:纸白(light)/ 炭黑(dark)双主题,单一强调色**朱砂红**;不用科技蓝、渐变、玻璃拟态、满页大圆角。
- UI 文本用系统字栈(中文 PingFang/Noto Sans CJK 栈,西文 system-ui);**站名与页面大标题用馆藏点阵字体自渲染**,像素风格只做点睛。
- 点阵呼应细节:覆盖率进度条用离散像素方块;分隔线 1px 实线或点线;数字用等宽/tabular。
- 严格排印网格与充足留白;暗色主题完整支持(canvas 反色联动)。
- 实现阶段加载 frontend-design 技能打磨具体视觉;本节原则为验收基准。

## 9. 工程、测试与 CI

- **技术栈**:Python 3.12(pyproject;uv 可用则用,否则 venv+pip;依赖 fonttools、freetype-py、Pillow)、Node 24、Astro 5、Svelte 5、TypeScript strict。
- 目录页「墨迹高」筛选取汉字墨迹高;无汉字的家族回退用 cap height 参与同一筛选轴。
- **测试**:
  - pytest:各解析器金样例(手工构造的小 BDF + bdftopcf 生成的 PCF 夹具)、度量口径用例、覆盖率计数用例、许可证指纹用例、字形包 writer 往返。
  - vitest:字形包解码器(与 Python writer 共享二进制夹具)、筛选纯函数、GlyphStore。
  - Playwright 冒烟:目录页渲染、筛选、样例编辑触发重绘、详情页字形网格、下载链接对 manifest 校验。
  - 实现全程 TDD(superpowers 流程)。
- **CI(GitHub Actions)**:job1 管线(按 fonts/ 哈希缓存)→ job2 Astro 构建 + 体积红线检查(≤900MB)→ Pages 部署;job3 下载物增量上传 Releases。PR 只跑构建与测试,不部署。
- **许可证**:代码 MIT;字体各归各的许可证;字表数据第三方声明。
- **i18n**:UI 文案 zh/en 类型化字典;字表名称/说明双语随数据文件。**所有英文翻译由 Opus/Sonnet 子代理完成(全局规则:Fable 不直接做翻译,含翻译复核)。**

## 10. 实施顺序

1. **管线核心**:BDF 解析 → 度量 → 覆盖率(先做总览+GB2312)→ 字形包 + 解码器。
2. **站点骨架**:Astro + 目录页 + 详情页,试点 5 家族打通端到端(ark-pixel、galmuri、baekmuk 四拆、UnifontEX 压力测试、一个 TTF 转制家族)。
3. **补全**:PCF 解析、全部覆盖率板块、许可证识别、预渲染/og、下载物+Releases、查字、字形网格。
4. **批量导入**:ingest 全量跑收集夹,出导入报告;风格标注清单交所有者复核。
5. **视觉打磨 + 双语 + CI/部署上线。**

每阶段完成判据与任务拆分见后续实现计划(writing-plans)。

## 11. 风险与既定处理

- **Pages 体积**:字形包总量预估 100–200MB(gzip 后),留有余量;若超线,先裁 SMP 之外的稀有分块按需化,再考虑二级 Release 托管。
- **PCF 旧编码映射**:无法可靠映射的字体降级展示并警告,不阻塞构建。
- **TTF 原生格点误判**:校验失败即不自动转制,进报告人工定夺。
- **Release 资产 URL 稳定性**:资产名含家族 slug 不含哈希,链接长期稳定;内容变化由 manifest sha256 表达。
- **构建时长**:增量缓存 + 并行解析;全量冷构建目标 < 15 分钟(CI)。
