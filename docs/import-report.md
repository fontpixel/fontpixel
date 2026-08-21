# 导入报告

生成时间：2026-08-21（由 pfc.ingest.run 生成，重跑覆盖）

- manifest 家族数：51
- 本次有变化：47；无变化跳过：4
- 文件写入：252；未变：44

## 本次导入/更新

- ba-ding-shi-wei-ti-16
- chang-ban-dian-song-12
- chang-ban-dian-song-16
- qiu-ye-yuan-ti-16
- ren-ou-fang-song-16
- xiu-zhen-xiang-su-ti
- zheng-ge-dian-hei-16
- zlabs-pixel-12px
- zlabs-diamondpix-16px
- zlabs-geopix-16px
- zlabs-roundpix-12px
- zlabs-roundpix-16px
- muzai-pixel
- xiaoya-pixel-classic
- cmex-ming
- wqy-unibit
- pixel-mplus
- tekuplus
- x5y8px-nega-clip
- x5y8px-nega-tape
- x8y12px-denki-chip
- x12y12px-maru-minya
- baekmuk-dotum
- baekmuk-gulim
- baekmuk-hline
- dos-myungjo
- dos-gothic
- dos-saemmul
- sam3kr-font
- dos-iyagi-boldface
- dos-pilgi
- miraero-normal
- neodgm
- neodgm-pro
- x10y12px-denki-chip-hangul
- x12y12px-maru-minya-hangul
- ark-pixel
- fusion-pixel
- fusion-bold-pixel
- jelly-pixel
- gnu-unifont
- retro-pixel-arcade
- retro-pixel-cute
- retro-pixel-petty-5h
- retro-pixel-petty-5x5
- retro-pixel-thick
- isas-song

## 错误

- neodgm-pro: NeoDunggeunmoPro-Regular.ttf 原生格点判定失败,不自动转制(可在清单中手填 ppem)

## 待人工决定

- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/Astro-2539--ZLabs-Bitmap-HC — 作者在 README 中明确说明本仓库已并入主仓库「Z Labs Bitmap 12px」(现名 Z Labs Pixel 12px,即本片段 zlabs-pixel-12px 家族的 HC 变体),仓库不再更新,内容重复,故跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/Astro-2539--ZLabs-Bitmap-JP — 同上,已并入 zlabs-pixel-12px 的 JP 变体,仓库不再更新,故跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/DWNfonts--Hexin-Pixel-Font — 仓库内只有偏旁部件 PNG、构建脚本与上游 k12x8 参考字体(Data/Fonts/ 下的是基础参考件,非「核心像素体」成品),README 说明预构建字体发布在 Codeberg Releases 页面,本次快照未抓取到,当前内容无法直接产出完整字体,故跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/44670--SourceHanSans-Pixel — 仓库仅含可变字体源(SourceHanSansSC-VF.otf)、C 头文件示例(examples/C/font.h)与专有二进制 .4FN 字库(16x15／12x11);无 BDF／OTB／kbitx,.4FN 为非常规格式,现有转换管线无法解析,故跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/larryli--u8g2_wqy — README 明确说明以「文泉驿点阵宋体」为源本转制给 u8g2 库使用(9pt/10pt/11pt/12pt/13px 与已收录的 wqy-bitmap-song 尺寸一致),内容重复,故跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/wixette--dotted-chinese-fonts — 字体是「文泉驿点阵宋体」经矢量化后再加工出的菱形／圆形／方形三种装饰点阵效果 OTF,已脱离原生像素网格、无法判定原生 ppem 供 convert="ttf" 使用,且字形血缘与已收录的 wqy-bitmap-song 重复,故跳过,留待人工评估是否作为装饰字体单独收录。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Japanese/ayamada--mplus-1mn-medium-16-fnt-tir — 仅有 libgdx BitmapFont「.fnt」+ distance field PNG 贴图格式(M+ 1m medium 的位图化衍生),不是 BDF/OTB/kbitx/TTF,当前转换管线不支持,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Japanese/code4fukui--shinonome-font — 经典东云(Shinonome)字体,但发布形式是 font_src.bit / font_src_diff.bit,需要仓库自带的 autotools + bit2bdf 工具链编译才能得到 BDF,仓库里没有现成 BDF/TTF;convert 只支持 otb/kbitx/ttf 三种,暂不支持「.bit」,先跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Japanese/emutyworks--8x8DotJPFont — 美咲フォント(Misaki Font)的 Arduboy 移植版,只有 PNG 原图与 C 头文件(misaki_font_f0/f1/f2.h),没有 BDF/TTF,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Japanese/hajimehoshi--mplus-bitmap-images — 只是把 mplus_f12r.bdf / mplus_j12r.bdf 渲染成的 PNG 图片,原始 BDF 已经通过 itouhiro--PixelMplus(pixel-mplus 家族)收录,属重复,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Japanese/hicchicc--NegaPico — x5y8pxNegaTape 的 PICO-8 游戏机改版,发布形式是 .p8 卡带代码 + PNG 精灵图,没有 BDF/TTF;原字体已经通过 x5y8px-nega-tape 家族收录,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Japanese/Tamakichi--Arduino-misakiUTF16 — 美咲フォント(Misaki Font)教育汉字子集的 Arduino C++ 库,只有 misakiUTF16FontData.h 头文件数据,没有 BDF/TTF,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Korean/arnoldligtvoet--hangul_bitmap — 只有 PNG 位图 + Jimp 专用 XML 描述文件(hangul.xml),不是 BDF/OTB/kbitx/TTF,而且本身是转发自 biud436/MV 仓库的衍生副本,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Korean/mushsooni--mulmaru — Mulmaru/MulmaruMono 只发布 OTF/TTF/WOFF2(以及 .pfp 源文件),而且这些文件只存在于 RELEASE-ASSETS 下的 Mulmaru.zip/MulmaruMono.zip 内,仓库目录树里没有解压出来的副本;当前管线 convert_take 只递归扫描仓库目录树、不会解开 zip,zip_take 又只做原样拷贝、不会调用 convert,现有 manifest 字段组合不出「zip 内 TTF→BDF」的转换路径,故跳过。README 说物마루与물마루 Mono 分别是变宽与等宽两种排布,一旦管线支持,建议合并成一个 family 用 zips 收两个 zip
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Korean/yangpa-onyon--Mallangche — README 明确说明目前只发布 PNG(png/jamo.png、png/syllables.png 等)且带抗锯齿,作者说明以后才会出其他格式,当前没有 BDF/TTF 可收,跳过
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/TakWolf--capsule-pixel-font — 胶囊像素字体（瘦高圆体风格）。仓库内无 RELEASE-ASSETS、无任何 zip/bdf，README 明确声明「该字体目前仅用于概念验证，尚未完工，暂无可用实例」。待上游正式发布后再收。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/TakWolf--pulse-pixel-font — 脉冲像素字体（瘦高黑体风格）。仓库内无 RELEASE-ASSETS、无任何 zip/bdf，README 明确声明「该字体目前仅用于概念验证，尚未完工，暂无可用实例」。待上游正式发布后再收。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/pixel-font-studio--fusion-poke-pixel-font — 为同人游戏「宝可梦无限融合」定制的字体，仅发布 TTF（normal/narrow/small 三变体 × 5 语言，无 BDF/OTB）。README 明确声明「为了适配 mkxp-z 字体渲染相关的一些特殊行为，本字体参数做了一些特殊处理，所以可能无法正常用于普通项目」，即字体度量做过非标准化的游戏引擎特调，不适合作为通用像素字体收录；且衍生自 fusion-pixel（已收）与 ark-pixel/boutique-bitmap-9x9/cubic-11/galmuri 等组件。建议跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/pixel-font-studio--mixed-maruminya-pixel-font — 混合咪喵像素圆体：整合 x12y12pxMaruMinya 系列的构建方案，定位与缝合像素类似。仓库内无 RELEASE-ASSETS、无任何发布产物；assets/fonts/ 下只有三个第三方源输入字体（x12y12pxMaruMinya.ttf、x12y12pxMaruMinyaHangul.ttf、ZLabsRoundPix_12px_M_CN.ttf，均为构建原料而非本项目产出的「混合」成品），需要运行仓库自带的构建脚本才能生成实际字体。待上游发布构建产物后再收。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/hajimehoshi--bitmapfont — Go 语言点阵字体库（bitmapfont v4）。实际发布产物 data/*.bin 是自定义 Go 二进制格式，并非标准字体文件，也没有 font.Face 之外的静态字体导出。仓库内确有 13 个 .bdf（+1 个 .ttf）在 internal/ 下，但全部是构建用的第三方组件副本：internal/ark 的 2 个 bdf 是 ark-pixel 12px 等宽子集（已收 ark-pixel 家族覆盖）；internal/galmuri 的 GalmuriMono11.bdf 是 galmuri 的子集（已收）；internal/baekmuk（Gulim）、internal/mplus（M+ Bitmap Fonts，obsolete）、internal/fixed（misc-fixed，Public Domain 经典 X11 字体）、internal/cubic11（Cubic 11 的 ttf）均为其它字体的第三方嵌入副本，各自更适合从其官方上游仓库收录（如在本次全量清单其它分片中）。顶层 LICENSE 为 Apache-2.0（仅覆盖 Go 代码），各嵌入字体许可证见 README（Baekmuk License、M+ Bitmap Font License「free softwares」、OFL、misc-fixed 为 Public Domain）。整体建议跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/olikraus--u8g2 — u8g2 是大型渲染库，仓库内 SELECTION-NOTE.txt 已说明只保留了 CJK/Unifont/WenQuanYi/GB 相关 bdf。实测 tools/font/bdf/ 下 10 个 bdf 中：wenquanyi_*.bdf（5 个，9pt/10pt/11pt/12pt/13px）与已收 wqy-bitmapfont 重复；unifont.bdf/unifont_upper.bdf/unifont_jp.bdf（3 个）与本片段新收的 gnu-unifont 重复；gb16st.bdf/gb24st.bdf（2 个）是 1988 年 Academia Sinica（ISAS）宋体点阵字体，许可宽松（允许使用/复制/修改/分发），字形本身有历史价值，但采用 GB2312-1980 GL 编码（COMMENT 内注明「高位字节为 0」的旧式双字节编码），ENCODING 并非 Unicode 码位，当前导入器无字符集转换能力，直接收录会导致码位与实际汉字错位、不可用。建议整体跳过；gb16st/gb24st 若未来要收，需先补一个 GB2312→Unicode 转码步骤，作为独立任务处理。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/scriptwide-fonts--scriptwide-bitmap-cjk-pd — 仓库为占位仓库：只有 LICENSE、README 与两个通用 BDF 加粗/斜体化 Perl 脚本（mkbold.pl/mkitalic.pl，公有领域工具，非字体本身），无任何字体文件。README 自述「公有领域 CJK 点阵字体」的姊妹仓库 scriptwide-bitmap-cjk 尚未创建（not created yet）。待上游放出实际字体后再收。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/trevorld--hexfont — R 语言数据包（CRAN 包 hexfont），内容是 GNU Unifont 源码分发里的 .hex 文件重新打包（inst/font 下 62 个文件，均为 .hex.xz 格式，非 bdf/otb/ttf），本质是 Unifont 的另一种再分发形式，与本片段新收的 gnu-unifont 家族重复；且当前导入器不支持 .hex 格式转换。建议跳过。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/DWNfonts--FullPixel — FullPixel：基于方舟像素字体制作、目标覆盖全部中日韩越统一汉字的 12x12 像素字体，README 自述「还在研发…」。仓库内无任何编译产物，只有构建脚本（ase2png.py、make.py、photo2bdf.py、build.bat）与一个 Aseprite 调色板样例文件（design/sample.ase），需要本地安装 Aseprite（付费软件）与 Bits'n'Picas 才能从头构建，无法直接收录。待上游发布可下载的字体产物后再收。

## 风格标注待复核

family.toml 中带 `# UNVERIFIED` 注释的 form/vibes 为导入时预填，
请逐一复核后删除该注释。
