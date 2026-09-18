# 免费开源点阵字体扩充审计 — 2026-09-17

本批收录标准为**免费取得、许可明确、可自由使用、修改和再分发的真正点阵字体**。收费项目直接排除，不列入等待购买或等待用户提供文件的队列。可选捐款而允许免费下载的项目可以收录。

首批新增 196 个家族、430 个点阵变体，后补三款后，本批新增 **199 个家族、433 个变体**，当前总计 **411 个家族、1,433 个变体**。Oldschool PC 曾临时撤下，用户了解发行版收录及公开争论后决定全部保留，已恢复源文件和导入清单。来源、原文件与 BDF SHA-256、编码与未编码字形数量见 [JSON 审计](style-expansion-audit-2026-09-17.json)。[来源审查](font-provenance-review-2026-09-17.md) 保留历史字形来源和许可依据，不作为排除清单。

## 收录与合并

- **Ultimate Oldschool PC Font Pack 2.2（已恢复收录）**：新增 131 个硬件设计家族，从官方 OTB 原生点阵导入。尺寸、加粗和硬件模式作为变体；六个已有 IBM 家族不重复添加。仅当逐字形点阵、字距、边界都证明 437 版是 Plus 版的子集时去重，其余均保留。原包 CC BY-SA 4.0 许可随字体分发；该声明针对 VileR 的重制成果，原始点阵的使用依据是作者对美国法的解释，不能视为各原厂授予开放许可，见上述专项复核。
- **Not Jam Font Pack**：29 个命名设计入口按同一设计合并成 27 个家族。不同尺寸可能拥有不同字符覆盖，全部保留。文件来自公开 GitHub 项目中的原版字体，审计记录锁定的提交与下载地址。作者 CC0 声明是字体许可依据，不沿用承载游戏项目的许可证。
- **Gossip / Gossip Icons**：各保留 Low、Med、High 三个 Pixel 变体；装饰针脚、圆角小块等形状不重复当作新的点阵设计。原字体的单位网格均为 50 units，em 为 1400，因此保留原生 28 ppem；三个分辨率的实际字面高度不同。按 OFL 保留名称条款，转换文件内部安装名分别为 **FontPixel Weft** 和 **FontPixel Weft Ornaments**，目录仍以原作者字体名标识来源。
- **Gilded Bitmap**：原始大写版与含小写的扩展版合并为一个家族的两个变体。不是简单子集：F、K、R、1、9 的点阵存在差异。扩展页误写的数字顺序按实际图片修正为 0–9。
- **Slime 字体包**：六个设计均收录，使用作者提供的单色 TTF，包括 Sol Schori 常规与粗体；不把两色阴影强行并入字面。
- **Frogatto & Friends**：Dialog、Label、Outline、Numbers 四个家族；Numbers 保留四个不同尺寸或轮廓变体。历史仓库 PNG 与 OpenGameArt 版本逐像素一致。按历史字符表完整映射拉丁文、西里尔文及存在的希腊文，修正 Outline 重复条目和两处宽度，并补全 Dialog 的四个箭头。前三张图的全部前景字面像素均纳入字形。Numbers 只去重逐像素相同的颜色版本。
- **MatrixType**：四个原始样式还原圆点后，其 291 个编码字符的位图、边界和字距一致，合并为一个点阵变体；每个圆点还原成一个像素。
- **monogram**：保留扩展字符集常规与斜体，基本字符集版不重复收录。
- **Pixtura12**：保留常规和窄体的全部字形及连字。常规版 EBDT 缺少 `@` 与 `_`；从同一 TTF 中取得相应字形，其中 `@` 在源文件本来就是空白。所有已有内嵌点阵与 FreeType 输出逐像素及字距核对一致，下划线从原像素轮廓补齐。

## 许可与筛选结论

| 项目 | 处理 |
| --- | --- |
| Royal Decree、Queens Quill、Noble Blabber、Fabled Font、Medieval Pixel Font、Spellbinding | 收费项目排除；不等待购买，不收录试用版。 |
| Antiquity Print | 排除当前取得的文件：镜像 TTF 的内嵌许可为 FontStruct Non-Commercial，作者当前页面为 CC BY 4.0；无法确认该具体版本的自由许可。 |
| AVA、Digit Tech、Erratic Cursive、Operation Napalm、Unitblock、Delta Block | 虽为开放许可，存在连续曲线或非像素网格的斜线、分段几何，不收录。 |
| Silver | 维持排除：CC BY 声明与收入/预算限制冲突。 |
| Pixel Operator | 实际源包许可为 **CC0**，不是名单中的 OFL。 |
| Pixelcastle | 原作者 [Leonhard Katschner 的发布页](https://www.behance.net/gallery/169528513/Pixelcastle-free-font)明确授予 OFL。Pixelbuddha 包误附 Tippa 的版权文字；保留原包供审计，正式分发采用正确作者版权与 OFL 全文。 |

此前下载受阻的 **Dank Depths、Fantasy Warrior、1307 已全部补齐导入**。用户提供了官方页面和下载包；许可、原生网格、完整字符与未编码图块检查见 [补充导入审计](style-expansion-audit-2026-09-17.md#supplementary-imports)。

Illusion Book、Unscii、Departure Mono、Cozette、Spleen、Galmuri、GNU Unifont、Ark Pixel、Fusion Pixel、Public Pixel 已有收录，保留原家族并细化 Vibes。

## 转换与覆盖检查

- 首批 430 个新 BDF 变体及后补 3 个变体逐一核对；原 TTF/OTF/OTB 的全部 Unicode cmap 项及全部实际字形名称均保留，无编码范围或语言子集裁切。
- 无 Unicode 编码的连字、组件、替代字形以 BDF `ENCODING -1` 保留，不杜撰 PUA 编码。Unicode 覆盖统计只计算实际编码字符。完整字形请使用 BDF 下载或 ZIP 中的 BDF；派生 TTF/WOFF2 导出仍沿用网站现有 Unicode 字符导出方式。
- PNG/BMP 按原像素提取；字符表、矩形、字距、基线及前景调色板均显式记录在 manifest 的 `sprite_maps`。Springwrite 的末尾 ß 按实际字形映射，空白占位不冒充已支持字符。Onix Fantasy 按原作者 Windows-1252 字符表，保留其将箭头与骷髅置于 `{`、`}`、`€` 位置的映射。
- OTB 解码补上 EBDT format 5 使用 EBLC 共享指标的处理，并保留未编码字形。独立生成的二进制回归测试覆盖共享指标、跨行位打包、cmap 别名和未编码字形。
- 已人工查看代表字体的像素预览，核对原生网格和转换后的轮廓。Vibes 是编辑分类，尺寸和文字系统仍由独立字段表达。

## 重现

原始文件位于相邻的 `../pixel-font-collection-fonts/`。JSON 审计为每个来源文件记录稳定下载地址（GitHub 地址锁定提交）、压缩包内路径及 SHA-256。下载解包到 manifest 指定的 `source` / `convert_take` 位置后，使用现有导入命令即可重现。来源为网页授予许可而未随包附正确文本时，`LICENSE-FONTPIXEL.txt` 保存作者署名、来源地址与完整标准许可。

```bash
.venv/bin/python -m opf.ingest.run --manifest ingest/manifest.toml --src ../pixel-font-collection-fonts --dest fonts
.venv/bin/python -m opf.build --fonts fonts --out site/public/data --downloads dist-downloads --cache .cache
npm run build --prefix site
```

## 新增家族明细

Oldschool PC 的 131 个新增家族逐项列于 JSON。其余新增家族如下；字形数为家族各变体分别保留，不相加冒充独立 Unicode 字符数量。

| 家族 | 变体 | 许可 | Vibes |
| --- | ---: | --- | --- |
| [Dank Depths](https://hexany-ives.itch.io/dank-depths-pixel-font) | 1 | OFL-1.1 | western-rpg, serif, experimental |
| [Fantasy Warrior](https://burpyfresh.itch.io/fantasy-warrior) | 1 | CC-BY-4.0 | blackletter, western-rpg, game-ui |
| [1307](https://intellikat.itch.io/1307-playdatepulp-font) | 1 | CC0-1.0 | handwriting, manuscript, western-rpg, handheld |
| [Ant Party](https://pleeze.itch.io/slimesfonts) | 1 | CC0-1.0 | micro, game-ui, western-rpg, rounded |
| [Bore Blasters](https://not-jam.itch.io/not-jam-font-pack) | 4 | CC0-1.0 | game-ui, block |
| [Breadcrumbs & Flakery](https://pleeze.itch.io/slimesfonts) | 1 | CC0-1.0 | micro, game-ui, western-rpg |
| [Corvid Conspirator](https://pleeze.itch.io/slimesfonts) | 1 | CC0-1.0 | micro, game-ui, western-rpg |
| [Counting Apples](https://pleeze.itch.io/slimesfonts) | 1 | CC0-1.0 | micro, game-ui, western-rpg |
| [Frogatto Dialog](https://opengameart.org/content/frogatto-friends-bitmap-fonts) | 1 | CC0-1.0 | game-ui, western-rpg |
| [Frogatto Label](https://opengameart.org/content/frogatto-friends-bitmap-fonts) | 1 | CC0-1.0 | game-ui, western-rpg |
| [Frogatto Numbers](https://opengameart.org/content/frogatto-friends-bitmap-fonts) | 4 | CC0-1.0 | game-ui, western-rpg, block |
| [Frogatto Outline](https://opengameart.org/content/frogatto-friends-bitmap-fonts) | 1 | CC0-1.0 | game-ui, western-rpg |
| [Gilded Bitmap](https://opengameart.org/content/16-bit-gilded-bitmap-font-with-lower-cases) | 2 | CC0-1.0 | serif, manuscript, western-rpg |
| [Gossip](https://gossip.cargo.site/) | 3 | OFL-1.1 | blackletter, textura, textile, manuscript |
| [Gossip Icons](https://gossip.cargo.site/) | 3 | OFL-1.1 | textile, symbols |
| [Gothic Pixelart Font](https://osadam.itch.io/gothic-pixelart-font) | 1 | CC0-1.0 | blackletter, manuscript, western-rpg |
| [Gothic Pixels](https://akezhar.itch.io/gothic-pixels) | 1 | CC0-1.0 | blackletter, manuscript, western-rpg |
| [Home Video](https://github.com/GGBotNet/fonts-cc0) | 2 | CC0-1.0 | vhs, crt-osd |
| [MatrixType](https://github.com/GGBotNet/fonts-cc0) | 1 | CC0-1.0 | dot-matrix, technical |
| [monogram](https://datagoblin.itch.io/monogram) | 2 | CC0-1.0 | game-ui, programming, elegant |
| [Not Jam Atomic](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | grunge, experimental |
| [Not Jam Blackletter](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | blackletter, manuscript, western-rpg |
| [Not Jam Chunky Sans](https://not-jam.itch.io/not-jam-font-pack) | 3 | CC0-1.0 | block, game-ui |
| [Not Jam Faithless](https://not-jam.itch.io/not-jam-font-pack) | 1 | CC0-1.0 | handwriting, western-rpg |
| [Not Jam Giant UI](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | game-ui, block |
| [Not Jam Glasgow](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | art-nouveau, elegant |
| [Not Jam Laika](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | constructivist, block |
| [Not Jam Mono Casual](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | handwriting, game-ui |
| [Not Jam Mono Clean](https://not-jam.itch.io/not-jam-font-pack) | 4 | CC0-1.0 | terminal, programming |
| [Not Jam Mono Crooked](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | crooked, game-ui |
| [Not Jam Mono Prophet](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | uncial, manuscript, western-rpg |
| [Not Jam Novel](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | serif, book |
| [Not Jam Old Peculiar](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | crooked, western-rpg |
| [Not Jam Old Style](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | serif, book |
| [Not Jam Pixel](https://not-jam.itch.io/not-jam-font-pack) | 1 | CC0-1.0 | micro, game-ui |
| [Not Jam Play](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | rounded, cute |
| [Not Jam Sci Mono](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | sci-fi, technical |
| [Not Jam Scrawl](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | handwriting, crooked |
| [Not Jam Serif](https://not-jam.itch.io/not-jam-font-pack) | 1 | CC0-1.0 | serif, book |
| [Not Jam Signature](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | handwriting, cursive |
| [Not Jam Slab Serif](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | slab-serif, book |
| [Not Jam Third Dimension](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | 3d, shadow |
| [Not Jam Toolkit](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | experimental, block |
| [Not Jam UI](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | game-ui, block |
| [Not Jam UI Condensed](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | game-ui, technical |
| [Olde Tome](https://ladyliefy.itch.io/olde-tome) | 1 | CC0-1.0 | blackletter, manuscript, western-rpg |
| [Onix Fantasy](https://opengameart.org/content/pixelart-fantasy-font-for-construct-2) | 1 | CC0-1.0 | block, western-rpg, game-ui |
| [Pixel Operator](https://www.dafont.com/pixel-operator.font) | 15 | CC0-1.0 | game-ui, dos, terminal |
| [Pixelcastle](https://www.behance.net/gallery/169528513/Pixelcastle-free-font) | 1 | OFL-1.1 | blackletter, manuscript, western-rpg |
| [Pixelzone](https://github.com/GGBotNet/fonts-cc0) | 1 | CC0-1.0 | retro-computer, game-ui |
| [Pixtura12](https://opengameart.org/content/pixtura12-medieval-pixel-font) | 2 | OFL-1.1 | blackletter, textura, manuscript, western-rpg |
| [Raster Forge](https://github.com/GGBotNet/fonts-cc0) | 1 | CC0-1.0 | micro, technical |
| [Scriptorium](https://fontenddev.com/fonts/scriptorium/) | 1 | CC-BY-4.0 | uncial, manuscript, western-rpg |
| [Sol Schori](https://pleeze.itch.io/slimesfonts) | 2 | CC0-1.0 | micro, game-ui, western-rpg |
| [Springwrite](https://opengameart.org/content/springwrite-16x16-pixel-font) | 1 | CC0-1.0 | blackletter, handwriting, manuscript |
| [Tiny RPG Badge](https://opengameart.org/content/tiny-rpg-font-kit-i) | 1 | CC0-1.0 | jrpg, game-ui |
| [Tiny RPG Brilliant Strength](https://opengameart.org/content/tiny-rpg-font-kit-i) | 1 | CC0-1.0 | jrpg, game-ui |
| [Tiny RPG Fine Fantasy Strategies](https://opengameart.org/content/tiny-rpg-font-kit-i) | 2 | CC0-1.0 | jrpg, game-ui |
| [Tiny RPG Forbidden Denizens](https://opengameart.org/content/tiny-rpg-font-kit-iii) | 1 | CC0-1.0 | jrpg, game-ui, blackletter, western-rpg |
| [Tiny RPG Mana Branch](https://opengameart.org/content/tiny-rpg-font-kit-ii) | 1 | CC0-1.0 | jrpg, game-ui |
| [Tiny RPG Mana Root](https://opengameart.org/content/tiny-rpg-font-kit-ii) | 1 | CC0-1.0 | jrpg, game-ui |
| [Tiny RPG Mana Trunk](https://opengameart.org/content/tiny-rpg-font-kit-ii) | 1 | CC0-1.0 | jrpg, game-ui |
| [Tiny RPG Necro Romance](https://opengameart.org/content/tiny-rpg-font-kit-iii) | 1 | CC0-1.0 | jrpg, game-ui, blackletter, western-rpg |
| [Tiny RPG Vampire Ire](https://opengameart.org/content/tiny-rpg-font-kit-iii) | 1 | CC0-1.0 | jrpg, game-ui, blackletter, western-rpg |
| [Undead Pixel Light](https://not-jam.itch.io/not-jam-font-pack) | 2 | CC0-1.0 | game-ui, block |
| [Varnished](https://pleeze.itch.io/slimesfonts) | 1 | CC0-1.0 | micro, game-ui, western-rpg, rounded |
| [Vergilia](https://fontstruct.com/fontstructions/show/2073919/vergilia) | 1 | OFL-1.1 | manuscript, serif, book, western-rpg |
| [Vyaz Pixel](https://github.com/GGBotNet/fonts-cc0) | 1 | CC0-1.0 | vyaz, manuscript |

## 首批验证

- 字体构建：408 个家族成功，无失败；站点数据 172.7 MB。
- Python：77 项测试通过；新增图片转换器在去掉弃用 API 后单独复测 3 项通过。
- 前端：68 项测试通过；Astro/Svelte 类型检查无错误。
- 浏览器：24 项通过，覆盖新 Vibes 筛选与 URL 保持、五个新字体预览和 BDF 下载，并回归 Google Fonts、Bitcount 合并与 MuzaiPixel。测试启动器同时完成正式 Astro 构建。
- 原有 18 条 Svelte 警告仍存在。空的旧 t-mat 来源目录被跳过，不在网站目录中。

## 三款补充导入后的验证

- 411 个家族、1,433 个变体；三个增量构建无失败。
- 三款重复导入写入 0 个文件，来源和 BDF 哈希匹配。
- 前端 schema / Vibes 共 3 项测试通过；浏览器共 11 项通过，正式 Astro 构建通过。
- Fantasy Warrior 的 11,172 个现代韩文音节完整；1307 的 95 个 ASCII 字符及 14 个未编码界面图块完整。

## 临时撤下时的验证记录（该撤下决定已取消）

- 当时为 274 个家族、1,105 个变体；完整字体构建成功。
- 撤下的 137 个家族均不在索引、详情数据和新构建的英文页面中。
- 正式 Astro 构建与 12 项浏览器测试通过，包括五个 Vibes 分组取消最后一项后仍保持展开、手动折叠、筛选 URL 保持、三款补充字体及韩文完整覆盖。

## 最终决定：全部保留

Oldschool PC 的 137 个家族、328 个变体全部恢复；Galmuri、Chusung、Lyusung 及其他项目继续保留。恢复后为 411 个家族、1,433 个变体。本批新增仍为 199 个家族、433 个变体。不存在针对本次历史来源审查项目的继续撤下指令。

## 恢复完成验证

411 个家族 / 1,433 个变体；恢复的 137 个家族 / 328 个变体与撤下前一致，1,513 个下载文件大小和 SHA-256 全部匹配。六种语言共 822 个恢复字体页面生成成功。正式 Astro 构建及 12 项浏览器测试通过，Astro/Svelte 检查零错误（保留既有 18 条 Svelte 警告）。Galmuri、Chusung、Lyusung 的变体未改动。

## Supplementary imports

使用用户提供的 `/home/chen/Downloads/tmp_fonts/` 中的官方页面快照和 ZIP。原文件未改动；页面、压缩包和解包文件另存于相邻来源目录 `../pixel-font-collection-fonts/direct-downloads-2026-09-17/style-expansion/`。逐文件 SHA-256 和压缩包内路径见 [完整 JSON 审计](style-expansion-audit-2026-09-17.json) 中这三个家族的 `sources` 与 `acquisition`。

| 字体 | 原生尺寸 | 编码字符 | 未编码字形 | 作者 | 许可 |
| --- | --- | ---: | ---: | --- | --- |
| [Dank Depths](https://hexany-ives.itch.io/dank-depths-pixel-font) | 16px | 67 | 1 | Hexany Ives | OFL-1.1 |
| [Fantasy Warrior](https://burpyfresh.itch.io/fantasy-warrior) | 11px | 11,716 | 472 | Douglas Vautour / Burpy Fresh | CC-BY-4.0 |
| [1307](https://intellikat.itch.io/1307-playdatepulp-font) | 8×8 | 95 | 14 | intellikat | CC0-1.0 |

许可证依据为各下载包的 OFL、README 或 CC0 文件，并与用户保存的作者页面核对。各家族分发完整许可和署名。此前这三项因下载验证阻挡而未收录，现在均已解决。

### 点阵与完整性

- **Dank Depths**：TTF 的 em 为 1024，每个像素为 64 units，转换为原生 16px BDF；轮廓不含曲线或斜线。全部 Unicode cmap 和未编码字形保留。编码字形共 3,890 个前景像素，与作者原始 PNG 的白色像素总数一致。
- **Fantasy Warrior**：作者 README 指定 11px；TTF 的 em 为 2048，像素边长因整数坐标舍入为 186/187 units。按 11px 原生尺寸转换并人工查看拉丁和韩文字形。全部 cmap、组件和未编码字形保留，没有把原本可见的字形转换为空白。现代韩文音节 U+AC00–D7A3 的 **11,172 个字符全部保留**，另有 94 个 Hangul Compatibility Jamo，以及原字体已有的拉丁、西里尔等字符。
- **1307**：直接从 160×64 的 Pulp PNG 提取 8×8 单元格，白色为字面，基线 7、下延 1、字距 8。前 95 格明确映射 U+0020–007E；后续 14 个界面图块以 `pulp-ui-<原图索引>` 命名，使用 BDF `ENCODING -1`，不赋予虚构 Unicode。图块索引为 100–107、120–122、140–142，其中全黑的中心图块 121 也保留。未使用的透明格不收录；完整 BDF 前景像素总数 **1,879** 与原 PNG 完全一致。[Pulp 官方文档](https://play.date/pulp/docs/)说明字体表同时包含界面图块。

所有原始字形都在 BDF 中；网站字符覆盖按实际 Unicode 编码统计。派生 TTF/WOFF2 沿用现有 Unicode 导出方式，完整未编码图块和组件请使用 BDF 或 ZIP 内 BDF。

### 分类与验证

- Dank Depths：`western-rpg`, `serif`, `experimental`；来源为像素轮廓 TTF。
- Fantasy Warrior：`blackletter`, `western-rpg`, `game-ui`；来源为像素轮廓 TTF。
- 1307：`handwriting`, `manuscript`, `western-rpg`, `handheld`；来源为原生 PNG 点阵。
- 三个家族的 manifest 重复导入均无错误，写入 0 个文件；来源、压缩包、BDF 哈希均匹配。
- 增量字体构建无失败；网站总计 **411 个家族、1,433 个变体**。
- 前端 schema 与 Vibes 的 3 项测试通过。
- `site/e2e/style-expansion.spec.ts` 的 11 项浏览器测试通过，覆盖三款新字体的预览、来源类型与 BDF 下载，另检查完整韩文音节覆盖、韩文输入无缺字及 1307 的 ASCII 映射和全部界面图块。
- Playwright 启动器同时完成正式 Astro 构建。上述数量是技术收录统计；Oldschool PC 的权利依据另见 [专项复核](oldschool-pc-license-review-2026-09-17.md)。
