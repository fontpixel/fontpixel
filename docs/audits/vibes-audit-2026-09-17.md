# Vibes 细分审计 — 2026-09-17

当前全站 411 个家族均已重新分配标签，共使用 53 个 Vibes。完整逐家族记录在 [JSON 审计](vibes-audit-2026-09-17.json)。这套分类允许一个字体属于多个风格；六种网页语言均有显示标签。筛选面板按五组折叠，初次载入时展开含选中标签的分组；随后由用户控制展开状态，取消最后一个标签不会自动收起分组。五组交互均已通过浏览器回归测试。

| 分组 | 代表标签与使用依据 |
| --- | --- |
| 电脑与游戏 | retro-computer、BIOS/CGA/EGA/VGA、microcomputer、demoscene、arcade、handheld、nintendo-ds、JRPG、western-rpg、game-ui。硬件名称只用于明确来源，Nintendo DS 对应 Galmuri。 |
| 终端与显示设备 | terminal、unix、programming、technical、industrial、sci-fi、retro-futuristic、VHS、CRT OSD、dot-matrix、Unicode fallback。Departure Mono、Home Video 和点式显示设计分别代表不同方向。 |
| 印刷与手稿 | blackletter、textura、bastarda、uncial、manuscript、vyaz、serif、slab-serif、book、typewriter、elegant。Jacquard、Jacquarda Bastarda、Scriptorium、Vyaz Pixel 等按具体字形区分。 |
| 艺术与手写 | art-nouveau、constructivist、grunge、handwriting、cursive、crooked、textile、sports、experimental。Not Jam Glasgow、Laika、Atomic、Signature 分别提供清楚的代表。 |
| 造型与纹饰 | rounded、block、outline、shadow、3d、symbols、micro、cute。例如 Not Jam Third Dimension、Gossip Icons、微型字体。 |

没有把所有建议机械添加成标签：缺少明确代表的细项暂不使用；CJK、中文、日语、韩语、多文字系统以及 3×5、8×8 等尺寸已有专门筛选，避免与 Vibes 重复。形态相近的 Glasgow Style 并入 Art Nouveau；NASA、机场屏等用途也不被假定为字体作者的具体历史来源。

`source_kind = "bitmap"` 表示直接来自 BDF/PCF/OTB、原生位图编辑文件、C 点阵数组或像素图片；`pixel-outline` 表示像素网格设计以 TTF/OTF 等轮廓格式发布，再按原生网格转成点阵。`source_formats` 另行记录实际来源容器，因此含 EBDT 的 TTF 也可以属于 bitmap。详情页会显示这项区别。

旧的 classic、retro-game、terminal-hardcore、decorative 显示标签保留兼容定义，现有家族尽量使用更具体的组合。Vibes 是编辑判断，不是由许可证、文件后缀或字符覆盖自动推断。

## 当前标签数量

| Vibe | 家族数 |
| --- | ---: |
| 3d | 1 |
| arcade | 2 |
| art-nouveau | 1 |
| bastarda | 1 |
| bios | 6 |
| blackletter | 14 |
| block | 15 |
| book | 25 |
| cga | 10 |
| constructivist | 1 |
| crooked | 3 |
| crt-osd | 1 |
| cursive | 1 |
| cute | 14 |
| demoscene | 1 |
| dos | 28 |
| dot-matrix | 4 |
| ega | 5 |
| elegant | 3 |
| experimental | 3 |
| fallback | 3 |
| game-ui | 106 |
| grunge | 1 |
| handheld | 2 |
| handwriting | 10 |
| jrpg | 12 |
| manuscript | 16 |
| micro | 31 |
| microcomputer | 1 |
| nintendo-ds | 1 |
| outline | 1 |
| programming | 71 |
| retro-computer | 144 |
| retro-futuristic | 1 |
| rounded | 16 |
| sci-fi | 2 |
| serif | 27 |
| shadow | 1 |
| slab-serif | 1 |
| sports | 1 |
| symbols | 6 |
| technical | 79 |
| terminal | 215 |
| textile | 6 |
| textura | 3 |
| typewriter | 1 |
| uncial | 2 |
| unix | 81 |
| vga | 5 |
| vhs | 1 |
| vyaz | 1 |
| web-pixel | 1 |
| western-rpg | 29 |
