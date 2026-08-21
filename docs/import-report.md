# 导入报告

生成时间：2026-08-21（由 pfc.ingest.run 生成，重跑覆盖）

- manifest 家族数：98
- 本次有变化：2；无变化跳过：96
- 文件写入：4；未变：414

## 本次导入/更新

- x5y8px-nega-clip
- x8y12px-denki-chip

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
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Korean/neodgm--neodgm-pro — NeoDunggeunmo Pro 官方定位即「跳出 8x16/16x16 网格」的比例宽度衍生字体,原生格点判定失败(实测确无统一格点),不适合栅格化收录;基础版 neodgm 已收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/1--font — 孤儿字体：JinzisheTongfang（金字社统方体），上游 https://gitee.com/typeface-cn/typeface_open_font ，未见于 Upstream-GitHub/Upstream-Direct/Maoken-Direct/Google-Fonts 任一目录（Gitee 源不在快照范围内）。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/4--font — 孤儿字体：JinzisheTongyuan（金字社统圆体），上游 https://gitee.com/typeface-cn/typeface_open_font ，同 1--font，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/316--LanaPixel — 孤儿字体：LanaPixel，上游 https://opengameart.org/content/lanapixel-localization-friendly-pixel-font ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/870--font — 孤儿字体：PoxiaoPixel（破晓像素），上游 https://forge.poxiao-labs.work/Fonts/fzg ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/898--font — 孤儿字体：KH Dot Akihabara 16（秋叶原），上游 jikasei.me KH ドットフォントシリーズ（http://jikasei.me/font/kh-dotfont/），未见于四目录任一处。注：scott0107000/FashionBitmap16 是基于该系列『兜町16』的中文化改作衍生字体，并非原版，不能替代。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/899--font — 孤儿字体：KH Dot Dougenzaka 12（道玄坂），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/900--font — 孤儿字体：KH Dot Hatcyoubori 16（八丁堀），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/901--font — 孤儿字体：KH Dot Hibiya 24（日比谷），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/902--font — 孤儿字体：KH Dot Kabutochou 16（兜町），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。注：scott0107000/FashionBitmap16 是基于此字体的中文化改作衍生版，非原版。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/903--font — 孤儿字体：KH Dot kagurazaka 12（神乐坂），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/904--font — 孤儿字体：KH Dot Kodenmachou 12（小传马町），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/905--font — 孤儿字体：KH Dot Ningyouchou 16（人形町），上游 jikasei.me KH ドットフォントシリーズ，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/992--UwU — 孤儿字体：UwU Matrix 16U（UwU 点矩黑，先行预览），上游 https://github.com/ChenhaoUwU/UwUMatrix ，与 Upstream-GitHub/ChenhaoUwU--ChenhaoRPFont（同作者但不同仓库/不同字体 ChenhaoRPFont）不是同一项目，未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/ZeoSeven-Webfonts/2136--x12y12pxMaruMinyaM — 孤儿字体：x12y12pxMaruMinyaM，上游 https://hicchicc.github.io/00ff/ ，是 Upstream-Direct/00ff 目录内 9 款 hicchicc 像素字体中唯一缺失的一款（该目录仅有其余 8 款），未见于四目录任一处。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/Geist-Font-v1.7.2 — Geist/GeistMono 为纯几何无衬线体/等宽体，与点阵无关（DESCRIPTION.en_us.html 自述『geometric typeface』，非位图字体），按简报要求确认非点阵字体不收录。GeistPixel（含 Circle/Grid/Line/Square/Triangle 五种点形与一个可变字体）虽名带 Pixel、外观点状，但对拉丁字母抽样做轮廓坐标最大公约数检查，结果均为非干净小整数网格（如 Circle/Line/Triangle 变体隐含 ppem≈52.6，Grid≈500，Square≈26.3，皆非典型像素尺寸），detect_native_ppem 对全部变体也判定失败，说明其『像素』只是圆点/方块/三角装饰造型的矢量近似，并非严格网格对齐的位图字体，性质与已 todo 的 oliverlalan/Doto 相同。建议整包不收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/Sango — 珊瑚字体是彩色像素马赛克风格字体，但技术实现为 OpenType-SVG 彩色字体与 COLR/CPAL 彩色字体（据 readme_sango.txt），并非传统单色点阵/位图字体；本收藏的 convert=ttf 栅格化管线基于 FreeType FT_LOAD_MONOCHROME 单色渲染，无法正确处理彩色图层，会破坏字体的核心视觉设计（马赛克色块）。目录内 Sango-JA-FALLBACK.ttf 单色回退版 detect_native_ppem 判定同样失败，不能确认是否为真正点阵网格。ZeoSeven-Webfonts 内另有 355(Sango-JA-FALLBACK)/356(Sango-JA-SVG) 的 WOFF2 切片镜像，性质相同不建议使用。建议本字体排除在本收藏之外，或后续为彩色字体设计单独的处理管线。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/curioustorvald--Terrarum-sans-bitmap — 已与 Upstream-Direct/Terrarum-Sans-Bitmap 合并处理（见上方 family 'terrarum-sans-bitmap'）。本仓库 HEAD 快照经核实不含任何编译产物（无 otf/ttf/woff/jar），只有源码/工程文件，故改用 Upstream-Direct 的直链下载包（内含同一份 TerrarumSansBitmap.otf 与 LICENSE.md），不单独收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/oliverlalan--Doto — 可变字体（wght+ROND 轴）。虽有静态 Black 实例 fonts/ttf/Doto.ttf，但那只是圆点显示体的 一个字重快照，本质是装饰性圆点字重字体而非严格像素网格字体（detect_native_ppem 判定失败）， 按简报要求可变字体一律 todo。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/petrvanblokland--TYPETR-Bitcount — 完全是可变字体（10 个变量 ttf，CRSV/ELSH/ELXP/slnt/wght 等多轴，无任何静态实例）， 按简报要求 todo，不写 family。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/RandomMaerks--Trmnl-Cubic — 并非真正的点阵/位图字体：README 强调的是'metrically square'（宽高比例接近正方形， 便于 ASCII-art 排版），而非位图网格设计。经坐标抽样检查（如字母 A/B 的轮廓点集）与预览图 （documentation/tc-a1.png）确认，字形是带 45° 斜切的矢量几何造型，边缘平滑非阶梯状；8 个 字重文件（otf+ttf × Bold/Medium/Regular/SemiBold）detect_native_ppem 全部判定失败（None）。 建议不收录，或人工复核后按'other/非像素'方式处理。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/Warren2060--ChillBitmap — GitHub 仓库快照内 4 个 zip（ChillBitmap7x_v2.500.zip、Version 2.200/2.300/2.400.zip） 解压后均只含 ChillBitmap7x（7px 版）。而 7px 版基于 GuanZhi 8px 修改，猫啃网标注'作者声明'， 审计已排除（见 EXCLUDED.csv ZeoSeven 360 行）。已通过审计的 16px 版（基于 Unifont，纯 OFL+GPL，INCLUDED.csv 359 行）不在本仓库快照、也不在 Upstream-Direct 内，唯一副本是 ZeoSeven-Webfonts/359--ChillBitmap-16px 的 WOFF2 切片镜像。建议后续从该镜像还原字体，或 联系上游单独取得 16px 版本编译产物。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/StevenLZH--IllusionBook — 已与 Upstream-Direct/IllusionBook-v1.0.2 合并处理（见上方 family 'illusion-book'）。 本仓库 HEAD 快照只有 FontForge 源文件（.sfd/.fea）与许可证，无编译产物，不单独收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/Warren2060--ChillMoonmono — 已与 Upstream-Direct/ChillMoonMono-v1.000 合并处理（见上方 family 'chillmoonmono'）。 本仓库 HEAD 快照只有 README 与 license 文本，无编译产物（README 提示'请查看 Releases'）， 不单独收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/Hansha2011--NanoDyongChyangSong — 已与 Upstream-Direct/NanoDyongChyangSong 合并处理（见上方 family 'nano-dyong-chyang-song'）。本仓库 HEAD 快照只有 README 与两张示意图，无编译产物，不单独收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/Hansha2011--NanoQyoanDaSong — 已与 Upstream-Direct/NanoQyoanDaSong 合并处理（见上方 family 'nano-qyoan-da-song'）。 本仓库 HEAD 快照只有 README 与一张示意图，无编译产物，不单独收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Google-Fonts/VT323 — VT323 的轮廓坐标不在任何格点上（gcd=1，设计即带软化边角的「像素风」矢量字体），不符合原生点阵收录口径，不转制。

## 风格标注待复核

family.toml 中带 `# UNVERIFIED` 注释的 form/vibes 为导入时预填，
请逐一复核后删除该注释。

## 待人工复核清单（构建后统计）

### 风格标注待复核（93 家，family.toml 内带 `# UNVERIFIED`）

00ff-donguriduel、00ff-gridgazer、00ff-headupdaisy、00ff-linelinker、00ff-scanline、00ff-scoredozer、00ff-solidlinker、00ff-thestronggamer、ark-pixel、ba-ding-shi-wei-ti-16、baekmuk-dotum、baekmuk-gulim、baekmuk-hline、bestten、boutique-bitmap-7x7、boutique-bitmap-9x9、chang-ban-dian-song-12、chang-ban-dian-song-16、chenhao-rp-font、chillmoonmono、chusung、clfn、cmex-ming、cubic-11、departure-mono、dos-gothic、dos-iyagi-boldface、dos-myungjo、dos-pilgi、dos-saemmul、dotgothic16、fairfax、fairfax-hax、fairfax-pona、fairfax-pula、fairfax-serif、fairfax-sm、fashionbitmap16、fusion-bold-pixel、fusion-pixel、gnu-unifont、illusion-book、jelly-pixel、k12x8、k6x8、k8x12、liora-chip-10x12、lyusung、miraero-normal、misaki、misekibitmap、monocraft、mplus-hzk-12、muzai-pixel、nano-dyong-chyang-song、nano-qyoan-da-song、neodgm、nightgazer-bitmap、pixel-mplus、pixeloid-mono、pixeloid-sans、press-start-2p、qiu-ye-yuan-ti-16、ren-ou-fang-song-16、retro-pixel-arcade、retro-pixel-cute、retro-pixel-petty-5h、retro-pixel-petty-5x5、retro-pixel-thick、sam3kr-font、silver、spleen、tekuplus、terrarum-sans-bitmap、tiny5、uranus-pixel、wqy-unibit、x10y12px-denki-chip-hangul、x12y12px-maru-minya、x12y12px-maru-minya-hangul、x5y8px-nega-clip、x5y8px-nega-tape、x8y12px-denki-chip、xiaoya-pixel-classic、xiu-zhen-xiang-su-ti、yarndings-12、yarndings-20、zheng-ge-dian-hei-16、zlabs-diamondpix-16px、zlabs-geopix-16px、zlabs-pixel-12px、zlabs-roundpix-12px、zlabs-roundpix-16px

### 许可证未识别（16 家，站点显示「许可证待确认」）

00ff-donguriduel、00ff-gridgazer、00ff-headupdaisy、00ff-linelinker、00ff-scanline、00ff-scoredozer、00ff-solidlinker、00ff-thestronggamer、chusung、clfn、lyusung、nano-dyong-chyang-song、nano-qyoan-da-song、press-start-2p、silver、xiaoya-pixel-classic

### 仅提供 BDF 下载（bdftopcf 转换失败，已记构建警告）

galmuri、isas-song、unifont-ex、x10y12px-denki-chip-hangul、x12y12px-maru-minya-hangul
