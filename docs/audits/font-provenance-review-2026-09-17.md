# 字体历史来源复核 — 2026-09-17

## 范围与当前操作

核对了目录元数据、可取得的本地上游 README / 许可文件，以及下面重点项目的一手网页和构建配置。恢复后的目录为 411 个家族、1,433 个变体。此记录区分作者声明、原始材料许可、历史设计参考与实际字形一致性；不是逐字形全球权利清查，也不将没有发现问题写成绝对原创保证。

用户在了解发行版收录及公开争论后，决定全部保留。Oldschool PC 曾临时撤下的 137 个家族 / 328 个变体已恢复源文件、导入清单、网站页面及下载，名单见 [历史操作记录](oldschool-pc-excluded-2026-09-17.json)。**Galmuri、Chusung、Lyusung 及其余已收录项目继续保留。** 本文中的来源记录不构成排除清单。

## 需要区别审查的已收录项目

| 项目 | 查到的实际来源证据 | 审查结论 |
| --- | --- | --- |
| Galmuri | [作者 Legal Stuff](https://github.com/quiple/galmuri#readme) 区分自行创作与 Nintendo DS 相关字形；以美国、韩国对字形和字体程序的区分说明可分发性。 | 7/9/11/14 常规版本不能仅凭 OFL 认定全部字形为原创或原厂授权。11 Bold、11 Condensed 则被作者明确声明为全部原创。未找到任天堂授予原始材料自由许可的证据；这不等于认定侵权。 |
| Chusung / 粗宋 | [作者页面](https://diaowinner.itch.io/chusung) 指向 X.Org gb16st。本站 Chusung-210529 的全部 94 个可见 ASCII 字形与 Oldschool ATI 8×16 完全一致。 | 中文原型有 ISAS 明确宽松许可；当前整字体另含与 Oldschool 一致的西文，不能只凭中文来源判断整字体。 |
| Lyusung / 柳宋 | [作者页面](https://diaowinner.itch.io/lyusung) 指向 X.Org gb24st。本站 Lyusung-210618 的全部 94 个可见 ASCII 字形与 Oldschool DOS/V ANK24 完全一致。 | 与粗宋同样需要区分中文和西文来源。 |
| font8x8 | [README Credits](https://github.com/dhepper/font8x8/blob/master/README) 明确来自 Marcel Sondaar 的汇编文件，并署名 IBM VGA 字体为 public domain。 | 这是上游整理者的公有领域声明，尚未找到 IBM 原始发布声明；不是全部由 Marcel Sondaar 或 Daniel Hepper 新设计。 |
| Press Start 2P | [作者发布页](https://www.zone38.net/font/#pressstart) 明确说明将 Namco Return of Ishtar 字体转为 TrueType，并扩充字符。Google Fonts 的 [介绍](https://github.com/google/fonts/blob/main/ofl/pressstart2p/DESCRIPTION.en_us.html) 也说明游戏字形来源。 | OFL 是转换及扩充作品的开放许可；不能将 Google Fonts 收录解释为 Namco 的原始授权。 |
| hurss 七款：DOS Myungjo、DOS Gothic、DOS Saemmul、DOS Iyagi Boldface、DOS Pilgi、Sam3KRFont、Miraero Normal | [作者 README](https://github.com/hurss/fonts) 自述从二进制点阵数据转换，CJK 来源包含 Hanme-hangul 和 jiskan16；Sam3KRFont 标为“三国志3字体”。 | 需要原始数据的逐项来源与许可；不能只凭整理项目的许可解决。README 说 MIT，而保留的 LICENSE.txt 为 OFL，另有版本许可记录需要澄清。不能推断每款都用了同一组汉字，Sam3KR 明确不含汉字。 |
| Unscii | [原始设计记录](https://github.com/viznut/unscii/blob/master/src/unscii.txt) 列明 Amiga、Atari、IBM、C64 等参考字体及历史伪图形；[MCR 字形源文件](https://github.com/viznut/unscii/blob/master/src/font-mcr.txt) 逐字形比较并选取 C64 游戏中的形状。 | 不是凭复古外观作推断，确有复刻/综合历史设计的依据；但不能由此直接断言它复制原字体程序或侵权。当前收录的七款不含 unscii-16-full，不应误称这些版本全部含有 full 版的 Fixedsys/Unifont 合并内容。 |

粗宋、柳宋的比对去除空白边缘及位置偏移，逐像素比较 U+0021–U+007E，**没有缩放、模糊匹配或抽样**，两者各为 94/94。没有要求字距或基线相同。它证明整套字面相同，不能单凭它证明文件之间的直接复制路径或法律权属。具体源文件路径、SHA-256 与码点见 [比对记录](chusung-lyusung-provenance-comparison-2026-09-17.json)。仅重新查看作者主页和 TTF 版权栏时证据不足，补充位图比对后才得到这一更明确的结论。

## Galmuri 的下游关系

- [Fusion Pixel](https://github.com/TakWolf/fusion-pixel-font) 明确使用 Galmuri 补充韩文。本地上游 `assets/configs/dump.yaml` 点名 Galmuri7、Galmuri9、Galmuri11、GalmuriMono7；不是仅仅在 README 推荐字体。
- [Fusion Bold Pixel](https://github.com/pixel-font-studio/fusion-bold-pixel-font) 是 Fusion Pixel 的算法粗体，不能因为名称含 Bold 就等同于作者声明原创的 Galmuri11 Bold。
- [QuanPixel](https://diaowinner.itch.io/galmuri-extended) 明确使用 Galmuri 与 Chill Bitmap，原名 GalmuriExtended；其 BDF 版权栏也署名 Galmuri。
- [PoxiaoPixel](https://diaowinner.itch.io/poxiaopixel) 明确合并 Fairfax、ZLabs、Galmuri，并说明保留三者几乎全部字形。

**上述关系不能自动转化为全部下游字形有同样问题。** Galmuri7 的例外清单不包含韩文，作者声明其韩文为原创；Galmuri9/11/14 的韩文则只有部分被列为非原创。因此应核对实际取用的版本、码点和覆盖优先级，不能仅按依赖家族名称一刀切，也不能通过删掉 ko 变体就假定移除了所有其他变体里的韩文。

## 没有理由仅因“旧系统”或“受启发”撤下的例子

- **Not Jam**：[作者主页](https://not-jam.itch.io/not-jam-font-pack) 发布 CC0，并亲自说明使用 BitFontMaker2 以及绘制字形图后用 Pixel Font Converter 构建字体。项目具有持续开发记录，部分字体提供像素源图和配置。现有证据支持作者自行制作，没有发现其从旧系统厂商字库转存的证据。可以按作者来源和 CC0 收录，不能承诺已经证明每一个像素绝无历史相似形状。
- **X.Org Adobe / DEC 与 ISAS**：本站原始 BDF 头部含原权利人的明确许可。Adobe/DEC 条款允许使用、复制、修改、分发和销售；ISAS 条款允许为任何目的使用、复制、修改和分发并保留版权及许可声明。旧厂商或研究所署名本身不是排除理由，不能将这些原始许可与第三方重新贴许可混为一谈。
- **Monocraft**：[作者 README](https://github.com/IdreesInc/Monocraft) 明确说明未包含 Minecraft 原游戏的资产或字体文件，并公开重绘字形配置。其 Minecraft 风格本身不足以证明来自游戏文件提取。
- **Obilic**：源 README 说受 Apple Chicago、IBM VGA 启发；仅此不足以确定是原始数据复制。
- **NeoDunggeunmo**：[上游 README](https://github.com/neodgm/neodgm/blob/main/README.en.md) 说明原始 DOS 字体由 Jungtae Kim 创作并以公有领域发布。应记录此具体来源；不能因为 DOS 风格就说来自微软。此轮没有独立取得 1990 年代最初发布文件，原始 PD 声明仍需与上游转述区分。
- **KH Dot**：当前附带 OFL，署名原设计师平木敬太郎。发布介绍说明是由原设计师允许开放再发布的旧 X68000 字体；本次官网抓取失败，不能将转载说明说成本次已直接读取的原厂授权。其旧商用历史也不能自动否定后来的合法重新许可。

其他排除的误报：这里的 Mona / Mona S 是 MonadABXY 的现代项目，不是早期基于微软字体的同名 Monafont；MuzaiPixel 源说明指向 k8x12，图片名包含 chusung 不等于采用粗宋；Illusion Book 作者邮箱出现 Mojang 不是采用 Minecraft 字形的证据；UnifontEX 对 Galmuri 外观的讨论不是直接合并 Galmuri 字体文件的证据；Ark README 推荐 Fusion 也不是 Ark 已依赖 Fusion 的证据。

## 最终收录决定

- **全部保留**：Oldschool PC 恢复全部 137 个家族、328 个变体；Galmuri 全部现有变体、Chusung、Lyusung 及其他已收录字体继续保留，不裁切或替换其字形。
- 收录判断综合作者的开放许可、原始材料可自由使用的依据，以及 Debian main、Nixpkgs、openSUSE 等发行版的正式收录记录。自由字体可以是衍生或复刻作品，不要求所有字形均由当前发布者原创，也不把缺少逐项原厂授权书自动等同于不自由。
- 如实保留原设计者、复刻者、转换者与混合来源的区别，遵守现有署名和许可证要求；不将这些字体描述为全部原创或保证绝无争议。
- 上文的历史来源与公开争论用于提供事实背景，不是待撤下指令。此前要求排除上述字体的临时建议已取消。
