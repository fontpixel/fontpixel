# itch.io FOSS 点阵字体导入审计（2026-09-18）

## 结果

用户提供的 24 个 itch.io 项目已全部收录，没有因质量、格式或许可问题排除任何一项。多字体包按独立设计拆分，同一设计的字重、间距和轮廓/投影效果则保留为同家族变体：

- 48 个目录家族；
- 75 个 BDF 变体；
- 48 个家族均有中英文描述、作者、itch.io 来源、许可说明、细分 `forms` 与多选 `vibes`；
- 所有轮廓源均按手工核定的原生像素网格转换，并保留 cmap 外可识别的字形。

原始输入是 `/home/chen/Downloads/tmp_fonts/downloads/` 中的 28 个文件和 `/home/chen/Downloads/tmp_fonts/webpages/` 中的 24 个页面快照。可重现快照保存在仓库相邻的
`../pixel-font-collection-fonts/direct-downloads-2026-09-18/itch-foss-pixel-fonts/`：`downloads/` 保留原下载，`webpages/` 保留页面，`files/` 是导入器使用的解包内容。

## 项目与家族对应

| itch.io 项目 | 目录家族 | 变体数 | 许可 |
| --- | --- | ---: | --- |
| [Monogram UA](https://dmitriy-shmilo.itch.io/monogram-ua) | `monogram-ua` | 1 | CC0-1.0 |
| [SG Font Collection](https://spicygame.itch.io/fonts) | `attomic`, `blocky-pixel`, `canned-pixels`, `chibi-mono`, `impactful-bits`, `micro-pixel-sg`, `nano-bits`, `nano-plus`, `nano-square`, `narrow-pixel`, `pixel-sans`, `quest-square`, `retro-sans`, `royalty-mono`, `rune-mono`, `scroll-pixel`, `superwide` | 19 | CC0-1.0 |
| [Pixuf](https://erytau.itch.io/pixuf) | `pixuf` | 1 | CC0-1.0 |
| [Thin Sans](https://enekoatxa.itch.io/thin-sans) | `thin-sans` | 1 | CC0-1.0 |
| [Lief](https://ladyliefy.itch.io/lief) | `lief` | 1 | CC0-1.0 |
| [Dyslexic Lief](https://ladyliefy.itch.io/dyslexic-lief) | `dyslexic-lief` | 1 | CC0-1.0 |
| [Kubasta](https://zichy.itch.io/kubasta) | `kubasta` | 1 | CC0-1.0 |
| [pirkkala](https://ottoojala.itch.io/pirkkala) | `pirkkala` | 1 | CC0-1.0 |
| [C-64 Font — Free](https://jamiecross.itch.io/c-64-font-free) | `c-64-fonts` | 2 | CC0-1.0 |
| [Sekaiju Font Collection](https://goburinbro.itch.io/sekaiju-font-collection) | `sekaiju-alpha`, `sekaiju-beta` | 2 | CC0-1.0 |
| [Canyon Racer Pixel Fonts](https://bbbbbr.itch.io/canyon-racer-fonts) | `canyon-racer-notify`, `canyon-racer-splash`, `canyon-racer-game-over`, `canyon-racer-sound-test` | 14 | CC0-1.0 |
| [Den Of Snakes Pixel Fonts](https://bbbbbr.itch.io/den-of-snakes-pixel-fonts) | `den-of-snakes-four-player` | 5 | CC0-1.0 |
| [SPLCF](https://def-the-dev.itch.io/splcf) | `splcf` | 1 | LicenseRef-PublicDomain |
| [5x7 Levee Pixel Font](https://flogram.itch.io/5x7-levee-pixel-font) | `levee-5x7` | 1 | CC0-1.0 |
| [Free Pixel Font Bundle](https://nimblebeastscollective.itch.io/magosfonts) | `mago1`, `mago2`, `mago3` | 3 | CC0-1.0 |
| [tinypixel](https://videodante.itch.io/tinypixel) | `tinypixel` | 1 | OFL-1.1 |
| [Cairopixel](https://ggbot.itch.io/cairopixel-font) | `cairopixel` | 1 | OFL-1.1 |
| [Pixelosopher](https://helianthus-games.itch.io/pixelosopher) | `pixelosopher` | 3 | OFL-1.1 |
| [Pix Romana](https://helianthus-games.itch.io/pix-romana) | `pix-romana` | 2 | OFL-1.1 |
| [minibyte](https://wqonart.itch.io/minibyte) | `minibyte` | 2 | OFL-1.1 |
| [Floppy Pixel Font](https://jdjimenez.itch.io/floppy-pixel-font) | `floppy-pixel` | 3 | OFL-1.1 |
| [3x5 Pixel Font Pack](https://mazeon.itch.io/3x5-pixel-font-pack) | `3x5-block`, `3x5-notched`, `3x5-rounded` | 6 | OFL-1.1 |
| [Capsigrany](https://enmarimo.itch.io/capsigrany) | `capsigrany` | 1 | OFL-1.1 |
| [innerlight serif pixel font](https://innerlightdev.itch.io/serif-pixel-font) | `innerlight-serif` | 2 | MIT |

SG 包内的 Blocky Pixel 常规/粗体与 Nano Square 实心/轮廓分别合并为一个家族。Canyon Racer 依界面功能拆为四种设计，Game Over 的粗体、3D 和等宽组合保留为八个变体。3x5 包依字形造型拆为 Block / Notched / Rounded，每种保留 Mono 与 Adjusted 两种间距。

## 分类与 Vibes

`forms` 表示字形类别，`vibes` 表示视觉气质与用途；两者均按实际字形和页面用例逐家族复核，没有用单一通用标签代替。

| 家族 | forms | vibes |
| --- | --- | --- |
| `monogram-ua` | sans | game-ui, programming, elegant |
| `attomic` | sans | sci-fi, retro-futuristic, technical, game-ui |
| `blocky-pixel` | decorative, sans | block, game-ui, western-rpg |
| `canned-pixels` | decorative, sans | block, arcade, game-ui |
| `chibi-mono` | rounded, sans | cute, rounded, game-ui |
| `impactful-bits` | sans | block, game-ui |
| `micro-pixel-sg` | sans | micro, game-ui |
| `nano-bits` | sans | micro, game-ui |
| `nano-plus` | rounded, sans | rounded, cute, game-ui |
| `nano-square` | decorative, sans | block, outline, game-ui |
| `narrow-pixel` | serif | elegant, technical, game-ui |
| `pixel-sans` | sans | game-ui |
| `quest-square` | sans | game-ui, technical |
| `retro-sans` | sans | retro-computer, game-ui, console |
| `royalty-mono` | serif | elegant, game-ui |
| `rune-mono` | decorative | sci-fi, technical, game-ui |
| `scroll-pixel` | serif, decorative | western-rpg, manuscript, game-ui |
| `superwide` | decorative, sans | sci-fi, sports, retro-futuristic, game-ui |
| `pixuf` | sans | micro, game-ui |
| `thin-sans` | sans | game-ui, technical, elegant |
| `lief` | serif | serif, book, game-ui |
| `dyslexic-lief` | sans | game-ui, rounded |
| `kubasta` | terminal, sans | game-ui, terminal, retro-computer, programming |
| `pirkkala` | script | handwriting, crooked, cute, game-ui |
| `c-64-fonts` | terminal | retro-computer, microcomputer, game-ui |
| `sekaiju-alpha`, `sekaiju-beta` | sans | nintendo-ds, handheld, jrpg, game-ui, crooked |
| `splcf` | sans | game-ui, block, retro-computer |
| `levee-5x7` | sans | technical, game-ui, sci-fi |
| `mago1` | sans | sci-fi, technical, game-ui, symbols |
| `mago2` | sans | micro, game-ui, symbols |
| `mago3` | rounded, sans | rounded, block, game-ui, symbols |
| `tinypixel` | sans | micro, game-ui |
| `cairopixel` | serif, terminal | slab-serif, typewriter, book, game-ui |
| `pixelosopher` | sans | elegant, sci-fi, game-ui |
| `pix-romana` | serif, decorative | serif, elegant, sci-fi, game-ui |
| `minibyte` | terminal, sans | micro, game-ui, terminal, programming |
| `floppy-pixel` | decorative, sans | block, outline, game-ui |
| `3x5-block` | sans | micro, block, game-ui, technical |
| `3x5-notched` | decorative, sans | micro, technical, game-ui |
| `3x5-rounded` | rounded, sans | micro, rounded, cute, game-ui |
| `capsigrany` | rounded, sans | rounded, cute, game-ui |
| `innerlight-serif` | serif | serif, game-ui, jrpg |
| `canyon-racer-notify` | sans | handheld, game-ui, outline |
| `canyon-racer-splash` | decorative, sans | handheld, arcade, sports, game-ui |
| `canyon-racer-game-over` | decorative, sans | handheld, arcade, 3d, shadow, game-ui |
| `canyon-racer-sound-test` | terminal, sans | handheld, game-ui, technical |
| `den-of-snakes-four-player` | decorative, sans | handheld, game-ui, outline, block |

## 像素尺寸与完整性

原生 ppem 不是根据文件名一律猜测，而是联合字体坐标、官方预览和实际像素对齐后确定。其中最容易误判的例子是 C-64：实心版是 6px，Pixel 版为保留每个原像素之间的空隙必须用 30px，它不是同一 6px 位图的普通放大。其他显著尺寸包括 Pixuf / Thin Sans / Levee 8px、tinypixel 7px、minibyte 4px、3x5 包 6px、Sekaiju Alpha 12px / Beta 8px；Canyon Racer 与 Den of Snakes 在 16px 字框中保留其官方 6×12、7×7、8×8 等墨迹尺寸。每个家族的精确 ppem 已写入 `ingest/manifest.toml`，也体现在 BDF 文件名中。

转换后按源字体 glyph order 逐文件核对 BDF `CHARS`；所有输入均保留完整。Cairopixel 是唯一个计数看似多 1 的例外：源文件有 900 个 glyph order 记录，但 cmap 有一个共用同一轮廓的附加码位，因此 BDF 正确产生 901 个编码/非编码条目，并非重复转换或丢字。Sekaiju 同时提供 `.fon` 与 TTF；收录选用同版官方 TTF，不重复导入 Windows 封装版。

## 许可判定

- Kubasta 当前 itch.io 正文和元数据都明确写 CC0，但包内较旧的 name 表仍写 Open Font License；目录依作者较新、更宽松的公开授权记为 CC0，冲突已写入家族许可备注。
- Mago 页面正文的 License 段明确写 CC0 Public Domain 并链接 CC0 1.0，itch.io 元数据栏却写 CC BY-SA；依用户指示与作者正文按 CC0 收录，冲突同样显式记录。
- Lief / Dyslexic Lief 的 itch.io 元数据是 CC0；正文的商用付费语句使用“please pay what you can”，按请求而非附加许可条件处理，并在许可备注中说明。
- SPLCF 保留作者原文的公有领域权利放弃，标记为 `LicenseRef-PublicDomain`，没有将它伪写成 CC0。
- innerlight 页面直接声明 MIT，家族内附标准 MIT 文本并保留作者名。其他带包内许可文件的字体优先保留上游文件；只有页面授权的 CC0 项目使用快照中的标准 CC0-1.0 全文。

## 验证

- 导入器：`imported=48 skipped=0 files=123 unchanged=0`；123 个文件由 75 个 BDF 与 48 份许可文本组成，家族元数据另行生成。Thin Sans、Kubasta 和 minibyte 的轮廓源声明了不正常的上下升部数值，导入器按字形实测范围自动修复；四个受影响的输出（minibyte 常规/斜体）均已视觉检查，没有裁切。
- 独立全批构建：`families=48 variants=75 cached=0`，零失败、零构建警告；预览 SVG、OG 图、BDF/PCF/TTF 下载均成功生成。
- 在第二个全空临时目录中仅依赖 manifest 和来源快照重导，48 个家族的全部 171 个目录文件与本次收录树逐字节一致；多变体家族的常规默认项与 Bold/Heavy 字重覆写也在重建结果中生效。
- 默认变体的 48 张卡片预览已组成接触表逐项视觉检查，未发现错位、裁切、笔画粘连或原生网格选错。
- 导入、构建、许可、变体与家族元数据测试：73 passed。
