# 导入报告

生成时间：2026-08-21（由 opf.ingest.run 生成，重跑覆盖）

- manifest 家族数：122
- 本次有变化：37；无变化跳过：85
- 文件写入：203；未变：396

## 本次导入/更新

- x5y8px-nega-clip
- x8y12px-denki-chip
- 4thd
- 5thelement
- bitbuntu
- bitocra
- cherry
- clearlyu
- creep
- ctrld
- dina
- dylex-terminal
- dylex-crawl
- gohufont
- kakwa
- leggie
- lode
- mplus-fixed
- mplus-helv
- mplus-qub
- mplus-sys
- orp
- siji
- sq
- tamsyn
- tamzen
- terminus
- tewi
- unscii
- uw-ttyp0
- xbmicons
- ibm-bios
- ibm-cga
- ibm-cga-light
- ibm-ega
- ibm-mda
- ibm-vga

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
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/Hansha2011--NanoQyoanDaSong — NanoQyoanDaSong 已从馆藏移除（字形质量不足，2026-08-30），此仓库快照本就只有 README 与一张示意图，无编译产物，不收录。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Google-Fonts/VT323 — VT323 的轮廓坐标不在任何格点上（gcd=1，设计即带软化边角的「像素风」矢量字体），不符合原生点阵收录口径，不转制。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-thestronggamer） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-donguriduel） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-linelinker） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-solidlinker） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-scanline） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-scoredozer） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-headupdaisy） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/00ff（00ff-gridgazer） — hicchicc「00ff」系列当前仍适用 00FF Original License，作者 GitHub 项目表将其标为 Original／proprietary license，2026 年正在逐步迁移至 SIL OFL 但尚未完成。其自定义条款虽允许商用、修改与再分发，但规定修改数据的版权归原作者、条款可不经通知变更，缺少标准许可的不可撤回性、下游授权传递与版本固定机制，因此归类为权限较宽的 proprietary 自定义许可，不能按作者宣布的「未来迁移 OFL」倒推当前文件。待其正式发布 OFL 版本后再收。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Maoken-Direct/7577（像素 Silver） — 作者页面一方面指定 CC BY 4.0，另一方面又要求「制作预算或收入超过 100,000 美元须联系取得许可」。CC BY 4.0 本身允许不限规模的商业使用且合规后不可撤回，两者相互冲突。在作者明确说明该门槛只是自愿联系请求、而非使用条件之前，不纳入严格自由字体集合。
- 待议：pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-Direct/NanoDyongChyangSong（纳米点墙宋） — README 允许免费使用、复制、修改、分发，但另写「不可为字体收费」，与自由许可要求的商用自由相抵触；仓库无完整 LICENSE，发布包 TTF 也缺版权与许可信息，且日文、繁体、韩文字形的上游来源未完整说明，无法认定为 MIT／HPND／OFL 中任何一种。存疑，排除。注意同作者的 NanoQyoanDaSong v2.0+ 为 OFL 1.1，曾收录，后因字形质量不足于 2026-08-30 移除。
- 待议：CJK-bitmap-fonts-open-source-2026-08-18/Chinese/DWNfonts--XiaoyaPixel-Classic（小雅像素） — itch.io 元数据显示 Code license: BSD 3-Clause，但仓库实际 LICENSE 与 TTF 内嵌许可均为 00FF 式自定义条款，二者冲突。该条款虽允许商用、修改与再分发，但许可可变更、修改版权归属特殊，只能算宽松自定义许可，不符合严格 libre 白名单标准。
- 待议：github-clones-2026-08-29/masaeedu-bitmap-fonts/bitmap/spleen — 已收录（slug spleen，来自 fcambus 官方仓库 https://github.com/fcambus/spleen，BSD-2-Clause），本仓库内的副本不再重复处理。
- 待议：github-clones-2026-08-29/masaeedu-bitmap-fonts/bitmap/mplus/mplus_cursors.bdf — FONT XLFD 名为 “cursor”，是 X11 鼠标光标字形集合，不是文本字体，不适合收入像素字体收藏，跳过。
- 待议：github-clones-2026-08-29/masaeedu-bitmap-fonts/bitmap/tamzen-font/bdf/Powerline*.bdf — 纯 Powerline 分隔符号补充字体（不含常规拉丁字形），是 Tamzen 的配套符号集而非独立设计，不单独收录。
- 待议：github-clones-2026-08-29/masaeedu-bitmap-fonts/bitmap/tamzen-font/bdf/TamzenForPowerline*.bdf — Tamzen 正文缝合 Powerline 符号的衍生版，与已收录的 tamzen 家族内容重复（仅多了符号字形），不单独收录。

## 风格标注待复核

family.toml 中带 `# UNVERIFIED` 注释的 form/vibes 为导入时预填，
请逐一复核后删除该注释。

## 2026-08-29 第三批收录

新增三个来源,共 38 个家族;全部为自由许可,授权依据逐族记录在 `family.toml` 的 `[license]` 块。

### masaeedu/bitmap-fonts(29 族)

按用户核定的 23 个目录收录,其中两处按「一个真实字体一个家族」的规则做了拆分:
`bitocra` 目录含 4 套不同设计(Bitocra／Bitbuntu／4thD／5thElement);
`mplus` 目录内 BDF 的 `FAMILY_NAME` 分别是 fxd／hlv／qub／sys,拆成
M+ Bitmap Fixed／Helv／Qub／Sys 四族。`spleen` 与已收录的 fcambus 官方版重复,跳过。
许可证覆盖 OFL-1.1、MIT、GPL-2.0／3.0、WTFPL、BSD-2-Clause、Tamsyn License、
M+ 自定义宽松许可与公有领域声明,均满足自由许可标准。

### farsil/ibmfonts(6 族)

IBM PC 文本模式 ROM 字库的 BDF 复刻:BIOS／CGA／CGA Light／EGA／MDA／VGA,
共 19 个 BDF。仓库 LICENSE 声明全部 BDF 为 CC BY-SA 4.0;像素复原归 VileR,
BDF 转换归 farsil(Marco Buzzanca)。

### code4fukui/shinonome-font(3 族)

東雲フォント。上游以 `.bit`(ASCII 点阵画版的 BDF)分发,按字符集拆目录并用 diff
表达派生字形,因此不能直接收录,需重建:用上游自带的公有领域 Perl 工具
`tools/bit2bdf` 与 `tools/bdfmerge` 还原各字符集 BDF,再按
latin1(ISO 8859-1 全部)＋ hankaku(仅 U+FF61–FF9F 半角片假名)＋ kanji(JIS X 0208 全部)
合并成单个 Unicode BDF。重建代码:`pipeline/opf/ingest/shinonome.py`,可重跑。

- 東雲ゴシック:12／14／16px 含汉字(约 7150 字形),18px 上游无汉字基底,仅半角与拉丁
- 東雲明朝:12／14／16px
- 東雲丸文字:上游仅提供 12px

**授权更正**:東雲フォント是 **Public Domain**(東雲フォントライセンス,2001,
The Electronic Font Open Laboratory),不是 MIT。日本法下无法在法律上放弃著作权,
故由 AUTHORS 列出的作者声明不行使权利,实质等同公有领域,明确允许自由改造、
转换格式、嵌入与再分发。收录时已按公有领域标注,并随字体附上 LICENSE 与 AUTHORS 原文。

### TakWolf/retro-pixel-font

早前已随第一批收录(arcade／cute／petty-5h／petty-5x5／thick 五族),
许可证为 OFL-1.1(自动识别,置信 auto-high),无需重复处理。

## 2026-08-31 第四批收录

来源：**Tecate/bitmap-fonts**（`bitmap/` 下 54 个字体目录）与
**IT-Studio-Rech/bdf-fonts**（48 个 BDF），外加为取得完整家族或权威许可证原文
而引入的三个上游仓库：`xorg/font/schumacher-misc`、`bluescan/proggyfonts`、
`NerdyPepper/scientifica`。新增 **37 个家族**（133 → 170）。

第三批只按核定的 23 个目录收录（经 masaeedu/bitmap-fonts 快照，内容即 Tecate 的
2020 年副本，仅少 scientifica 一个目录）。本批把两个仓库剩余条目逐个复核，
自由许可的收录，其余记入下方「不予收录」。

### 收录明细

- **artwiz-aleczapka（14 族）**：anorexia／aqui／cure／drift／edges／fkp／gelly／
  glisp（含粗体）／kates／lime／mints（mild+strong 两档）／nu／smoothansi／snap。
  目录内 16 个 BDF 是 14 套彼此独立的设计，按「一个真实字体一个家族」拆开。
  **授权**：仓库快照无 COPYING，BDF 的 COPYRIGHT 只写 “artwiz, fixed by aleczapka”；
  依据 Fedora 的 artwiz-aleczapka-*-fonts 系列包（license 字段 GPL-2.0-only，
  Fedora 逐包做许可审查）与 Gentoo 的 media-fonts/artwiz-aleczapka-*（LICENSE=GPL-2）
  判定为 GPL-2.0-only，confidence=manual，不附许可证文件。
- **jmk-x11-fonts → Neep（13 变体）＋ Modd（4 变体）**：GPL-2.0-or-later（包内 README
  的 “Copying, Copyright, and Open Source” 一节写明）。目录里 223 个文件中真正的成品
  只有这 17 个：`neep-{pre,post}-ampersand-*`（38／89 字形）与 `neep-ampersand[-alt]-*`
  （1 个字形）是拼字体用的构建碎片，`*-part-*`（128 字形，Latin-1 上半区）与完整版重复，
  均不收。Neep 每个字面上游按 ISO 8859-1/2/9/15 拆成四份，已用 `[merge]` 合并成
  单一 Unicode 变体。
- **Neep Alt 不收**：整套 13 个字面只有 `&` 一个字形与 Neep 不同（作者说非美国用户
  可能偏好传统写法）。XLFD 的 FAMILY_NAME 虽为 “Neep Alt”，但显然是同一套设计；
  收进来只会让家族页多 13 个几乎一样的变体、下载物翻倍。同 `TamzenForPowerline`
  的处理口径。
- **stlarch 系（4 族）**：ohsnap（8 变体）／termsyn（8）／terminusmod（1）／
  terminusmodx（2）／stlarch 图标字体（1），GPL-2.0-only，README 与 PCF 的 COPYRIGHT
  属性双重佐证。ohsnap 与 termsyn 只收 ISO 10646 版本，上游的 ISO 8859-1/-2 版、
  带状态栏图标的版本与主机控制台字体属重复，不收。
- **tamsynmod（8 变体）**：GPL-2.0-or-later。发布包内只有 8 个 PCF、无任何说明文件，
  授权由三条互证：PCF 的 COPYRIGHT 属性为 “GPL”（未写版本）；同作者其余四个包的
  README 均写 “Released under GPLv2 license.”；被改作的 Tamsyn 其许可证原文
  “You are hereby granted permission to use, copy, modify, and distribute it as you
  see fit.” 本身即无条件允许修改再分发。
- **Proggy（3 族）**：Proggy Clean SZ／Square SZ／Tiny SZ，MIT（Tristan Grimmer）。
  字体与许可证均改从权威上游 bluescan/proggyfonts 取。上游另有不带斜杠零的版本与
  CP／BP 编码变体，与收录版仅个别字形不同，不重复收。
- **Coding Font Tobi**：MIT（Copyright (c) 2006 Tobias Werner）。此前一度判为
  「无许可、不予收录」，实为误判——许可证在 proggyfonts 仓库
  `Contributed/CodingFontTobi.zip` 内自带的 Licence.txt 里。该仓库 README 说明
  投稿字体各自适用包内自带许可证，不套用仓库根目录的 MIT。
- **其余单族**：envypn（MirOS，2 变体，已合并 ISO 8859-1/-2 两个切片）、
  erusfont（WTFPL）、haxor（GPL-2.0+，7 变体）、psevdoazbuka（GPL-2.0+）、
  lemon（WTFPL，已合并 ISO 8859-1 与 ISO 10646 两份）、uushi（WTFPL）、
  progsole（MIT）、scientifica（OFL-1.1）。
- **Schumacher Clean（31 变体）**：HPND，从 xorg 上游 `font-schumacher-misc` 收全套，
  而非只收 bdf-fonts 里那一个孤立的 `clR6x12.bdf`（两者字节一致）。
- **Tom Thumb**：CC0-1.0。判定依据是作者公开页面：Robey Pointer 写明本字体改自
  Brian Swetland 的字体，并在更新中写道 “Brian has authorized his font to be released
  under the CC0 or CC-BY 3.0 license.”。**注意** bdf-fonts 的 README.md 称其为 MIT
  并链到 http://vt100.tarunz.org/LICENSE ，但该链接实为 vt100 项目
  （Brian J. Swetland／Vassilii Khachaturov，1999）的 BSD-3-Clause 声明，未提及本字体，
  不能作为授权依据；BDF 的 COPYRIGHT 字段也只有一个没有权利人的 “MIT” 字样。
- **Adobe Helvetica（helvR12）**：HPND，授权原文逐字写在 BDF 的 COMMENT 块内。
  只收这一个字面；Adobe 的 X11 位图全套（Helvetica／Courier／Times／
  New Century Schoolbook）不在本次两个来源仓库范围内。

`form` 字段按实测的 SPACING／PIXEL_SIZE 判定（等宽→terminal，比例→sans，
图标→decorative），故未打 `# UNVERIFIED`；`vibes` 仍为人工预填。

### 不予收录

以下 16 个 Tecate 目录经复核不符合收录标准（授权须明确允许使用、复制、修改、
再分发并允许商用，且须明确适用于收录的这份文件）：

- **gomme** — BDF 的 COPYRIGHT 字段写死 `(CC BY-NC-SA 4.0)`，NC 条款禁止商用。
- **boxxy** — 只授予「复制与分发（含商用）」，未提修改权，且 COPYRIGHT 写
  “Designer of this font retains full rights under the law”。
- **gilesorr** — 目录内混有 `Copyright Bigelow & Holmes 1986, 1985.`（Lucida）等
  第三方版权，来源链不干净。
- **raize**、**kourier** — 商业软件（Raize Software／SemWare）附赠字体，freeware 非自由。
- **opti**、**pixelcarnage**、**speedy**（及 archives 内的 **CG Mono**、**Crisp**）——
  proggyfonts.net 投稿区转载的第三方字体；上游 README 说明投稿字体各自适用包内
  自带许可证，而这几款的 zip 内**没有**许可证文件。
- **sgi**、**dweep**、**knxt**、**lokaltog-fonts**、**montecarlo**、**trisk**、
  **zevv-peep** — 只有一行 COPYRIGHT 署名或干脆没有，上游亦无 LICENSE，授权无法认定。

IT-Studio-Rech/bdf-fonts 中未收的还有 `logisoso46.bdf`（由来源不明的 Logisoso.ttf
经 otf2bdf 转制，原 TTF 许可未知）与 `knxt.bdf`（同上，上游无 LICENSE）。该仓库
README.md 声称「除 tom-thumb 外全部为 public domain」，此说只对其中的 misc-fixed
部分成立，后加的 spleen／creep／scientifica／Haxor 等各有各的许可证，不能照搬。

### Adobe 的 X11 位图字体（5 族，2026-08-31 补收）

第四批原本只收了 IT-Studio-Rech/bdf-fonts 里那个孤立的 `helvR12.bdf`。复核后改为
按 Schumacher Clean 的做法从 xorg 上游收全：`font-adobe-75dpi` 与 `font-adobe-100dpi`
两个仓库，Helvetica／Times／Courier／New Century Schoolbook 各成一族。

两套是同一设计按 75dpi 与 100dpi 渲染的不同像素档（75dpi 给 8／10／12／14／18／24px，
100dpi 给 11／14／17／20／25／34px，只重叠一档），文件名却完全相同——
`helvR12.bdf` 在 75dpi 是 12px、在 100dpi 是 17px。按本站口径尺寸不同即同族变体，
因此合成一族；为此给导入器加了 `take_from`（`{前缀 = [模式...]}`，落地时给文件名
加前缀区分），否则两套会互相覆盖。四族各 48 个字面（4 款式 × 12 档），全部 ISO 10646、每面 756 字形。

**Symbol 未收**：同目录的 `symb*.bdf` 用 `CHARSET_REGISTRY "Adobe"` /
`CHARSET_ENCODING "FontSpecific"` 分发——Adobe 自有的符号编码，不是 Unicode。
`decode_cp` 没有对应映射，收进来 12 个字面全是零字形。已改记为 `[[todo]]`：
要收录须先补一张 Adobe Symbol→Unicode 映射表（希腊字母与数学运算符，
Adobe 与 Unicode 联盟均有公开对照表），作为独立任务。这不是授权问题，
其许可证与同目录其余 Adobe 字体相同。

**顺带补上的护栏**：这次是人工发现空字体的——管线原本会把 12 个零字形变体
照常发布，站上出现一张空白家族卡片，覆盖率全 0，没有任何报错。现在
`build` 里加了硬性检查：任一字面解析后字形数为 0 即让整族构建失败，
由既有的单家族隔离记进报告，绝不发布。

许可证为两个仓库内容相同的 COPYING：Adobe 与 DEC 的 HPND 式声明，明确授予
「为任何目的使用、复制、修改、分发与出售，且无需付费」。Debian 的
xfonts-100dpi／75dpi 与 Fedora 的 xorg-x11-fonts 三十年来即按此条款分发。

**未采用的另一来源**：Markus Kuhn 的 ucs-fonts 另发布过扩到更大字符集的版本
（bdf-fonts 里那个 helvR12.bdf 即是，1998 字形 vs xorg 的 756），但只覆盖个别字面。
混进来会让同一家族内的字符集覆盖参差不齐，故统一采用 xorg 版本，此处记录备查。

### 关于字体名里的第三方商标

本站的收录判定**只针对著作权授权**。有些字体名含第三方注册商标：

- **指称性使用（照原名收录，不改名）**：`ibm-bios`／`ibm-cga`／`ibm-cga-light`／
  `ibm-ega`／`ibm-mda`／`ibm-vga`（IBM® 属 IBM Corp.，VileR 的复刻，名字说明字形
  来自哪块硬件 ROM，没有别的诚实叫法）；`adobe-helvetica`／`adobe-times`／
  `adobe-courier`／`adobe-new-century-schoolbook`／`adobe-symbol`
  （Helvetica® 等属 Monotype）；`gnu-unifont`（Unifont 本身就是官方 GNU 软件包，
  属授权使用）。
- **擦边的造词（风险很低，记录备查）**：`bitbuntu`（影射 Ubuntu®，Canonical）、
  `monocraft`（影射 Minecraft®，Mojang／微软）、`yarndings-12`／`yarndings-20`
  （影射 Wingdings®，微软；但为 Google Fonts 发布，已过其法务）、
  `5thelement`（1997 年电影名，弱保护且商品类别无关）、`tewi`（东方 Project
  角色名，ZUN 的二创政策极宽松）。
- `dos-gothic`／`dos-myungjo`／`dos-pilgi`／`dos-iyagi-boldface`／`dos-saemmul`
  中的 “DOS” 是通用词（微软的商标是 MS-DOS），不在此列。

结论：**一个都不改名**。改名既去不掉字体文件内部 XLFD／FAMILY_NAME 里的商标串，
又会让目录失去识别价值。立场已写进站点「关于」页的免责声明一节：照原名收录不代表
商标权利人的背书或与其存在关联。

### 顺带修正的既有问题

- **导入器模式歧义（10 个家族）**：`take`／`convert_take`／`license_files` 原本只按
  文件名 glob 匹配并递归全目录，上游在不同子目录放同名文件时会全部命中、后者静默
  覆盖前者，导致每次重跑都重写、且实际收录的是哪一份取决于排序。现已支持带 `/` 的
  路径模式（根目录文件用 `./NAME` 锚定），并在命中同名文件时报错。受影响的
  zlabs 系、wqy-unibit、hicchicc 系、tiny5、monocraft 已逐条钉到**当前实际生效的
  那一份**，产物零变化。修正后全量导入 `imported=0`，完全幂等。
- **boutique-bitmap-7x7／9x9**：这两个 slug 早前已人工合并为 `boutique-bitmap`
  并删除，但清单里的 `[[family]]` 条目还在，全量重跑会把它们重新建出来。现已改成
  `[[todo]]` 条目并写明原因。
- **自报单字节字符集、实为 Unicode 编码的字体（4 个家族，找回 1437 个字形）**：
  `lemon.bdf` 声明 `CHARSET_REGISTRY "ISO8859"`，实际 ENCODING 最大到 65379；
  管线照它自报的单字节字符集解码，把码位 >0xFF 的字形全部当作「无法映射到
  Unicode」丢弃——1030 个字形只剩 191 个。同样情形的还有 bitocra（丢 335）、
  bitbuntu（registry 甚至拼成 `iSO8859`，丢 253）与 envypn（丢 10）。
  单字节字符集的码位上限就是 0xFF，出现更大的值只可能是字体把 registry 写错了，
  唯一合理的解释是它其实按 Unicode 编码。`decode_cp` 现在对
  iso8859／koi8／ascii／iso646 这几类单字节 registry 做特判：>0xFF 的码位按
  Unicode 原样透传并留一条说明，不再丢弃。
- **尚未处理**：双字节传统 CJK 编码仍有 3897 个字形被丢弃
  （baekmuk 系的 ksx1001.1997、isas-song 的 GB2312.1980、
  pixel-mplus 与 tekuplus 的 jisx0208.1990）。这些是各编码里本就未分配或属
  用户自定义区的码位，与上面的「registry 写错」性质不同，不能照搬同一个修法，
  需要逐个编码单独核查，留作独立任务。
- **移除 `commercial` 字段（2026-08-31）**：该字段逐字体记录"是否可商用"，但本站的收录
  标准本身就要求授权明确允许商用，站上不可能存在不可商用的字体——它恒为真，是冗余。
  更糟的是它并不可靠：`licenses.py` 的 `COMMERCIAL_OK` 白名单没收裸 GPL 与
  `LicenseRef-Baekmuk`，导致 9 个自动识别的家族（wqy-bitmap-song／wqy-unibit／
  unifont-ex／uranus-pixel／nightgazer-bitmap／baekmuk 四族）落到 `null`「未知」，
  与站点「每一款都可放心商用」的说法自相矛盾——而这些许可证全都允许商用。
  现已从 `LicenseInfo`、构建产物、`family.toml`（96 个文件）、清单、站点 zod 契约
  与五语 i18n（`commercialOk` 是删除商用筛选器时漏下的死词条）中一并移除。
- 导入器生成的 `family.toml` 模板此前只有中文字段，缺 `name_en`／`authors_en`／
  `description*`／`aliases`／`confidence`／`[merge]`／`[variants]`，与仓库里既有的
  125 个 `family.toml` 形制不一致，需逐个手补。模板已补齐，清单现在是这些字段的
  唯一事实源。

## 2026-08-31 第五批收录（官网／itch.io 直接下载）

新增 **12 个家族**，来源为用户提供的官网与 itch.io 页面快照及发布包。
素材落在 `direct-downloads-2026-08-31/`，含各站页面 HTML 快照备查。

### KH ドットフォント（8 族 15 变体）—— 解掉此前 8 条孤儿 todo

`jikasei.me/font/kh-dotfont/` 的 khdotfont-20150527。此前第二批曾把秋葉原16／道玄坂12／
八丁堀16／日比谷24／兜町16／神楽坂12／小伝馬町12／人形町16 记为「孤儿字体」——
它们只在 ZeoSeven 的 webfont 切片里出现过，四个来源目录里都没有。这次拿到官方发布包，
全部收录。

**授权**：OFL 1.1。发布包附许可证全文，README 明写「SIL Open Font License 1.1 のもとで
使用することができますので、商用利用などにおいても特に制約なくお使い頂けます」。
字形著作权归平木敬太郎，TrueType 化由自家製フォント工房完成。这批字体 1991–1996 年
为 X68000 设计，原以『電脳フォント』系列商业授权销售，TrueType 化后经作者同意
改以 OFL 自由发布。

**按设计分族**（上游称 15 書体，本站按「尺寸／假名改款＝同族变体」归并为 8 族）：

| 家族 | 风格 | 变体 |
|---|---|---|
| 小伝馬町 Kodenmachou | 角ゴシック | 12、12-Ki（幾何学的カナ）、12-Ko（小かな）、16、16-Ki |
| 神楽坂 Kagurazaka | 明朝体 | 12、16 |
| 道玄坂 Dougenzaka | 太明朝体 | 12、16 |
| 日比谷 Hibiya | 明朝体 | 24、32 |
| 秋葉原 Akihabara | 丸ゴシック | 16 |
| 人形町 Ningyouchou | 教科書体 | 16 |
| 八丁堀 Hatchoubori | 隷書体 | 16 |
| 兜町 Kabutochou | ファンテール | 16 |

各族均含 JIS 第二水准全部汉字（7200–7600 字形）。站上已收的几款中文点阵字体正是
以它们为底改作的：长坂点宋←道玄坂、八丁饰尾体16←八丁堀16、FashionBitmap16←兜町16、
秋叶圆体16←秋葉原16、人偶仿宋16←人形町16。

**技术要点**：这批 TTF 内嵌等倍点阵（EBLC／EBDT），按标称档位栅格化时 FreeType 会
直接取内嵌位图而非栅格化轮廓——实测 16 个抽样字形中 10 个与纯轮廓栅格化结果不同，
说明取到的确实是内嵌位图。**但 `detect_native_ppem` 对这批全部返回 64**
（upem 1024 ÷ 16 单位格），照它转制会得到 64px 的巨物；必须逐文件手填 ppem。
为此给导入器加了 `[family.ppem]` 表（`{文件名 = 档位}`）——原先 `ppem` 是家族级
单值，装不下道玄坂 12／16 这种一族多档的情况。

### GGBotNet（4 族）

- **Public Pixel** —— 8×8 等宽，1324 字形覆盖 98 种语言的拉丁／希腊／西里尔。CC0-1.0。
- **Pixtile** —— 8px，385 字形覆盖 52 种语言。CC0-1.0。
- **3x3 Mono** —— 3×3 格点、4px 字面，91 个设计字形（cmap 覆盖 280 个码位，
  多个码位共用同一形状是这个尺寸下的必然）。CC0-1.0。
- **QuinqueFive** —— 5×5 等宽，1047 字形覆盖 58 种语言。OFL-1.1，
  保留字体名 “QuinqueFive”。`detect_native_ppem` 判定失败，按上游
  「Use it only in sizes multiples of 5px」手填 ppem=5。

三款 CC0 的判定依据是发布包内 CC0 1.0 全文＋字体 name 表的 License 字段＋itch.io 页面，
三处一致。

### 不予收录：Silver（Poppy Works）

依用户提供的 itch.io 页面快照重新复核，**结论与此前 Maoken-Direct/7577 一致，
条款一字未改**：

> **Free\* License** — Attribution 4.0 International (CC BY 4.0) …
> \* However, if the budget of your production exceeds $100,000 USD in total spend
> or earnings, or if you require urgent support, please contact hello@poppy.works
> to license this font.

CC BY 4.0 本身允许不限规模的商业使用，且合规后不可撤回；而该星号把预算门槛写成了
「Free\* License」的组成部分（要求另行 license this font），二者直接冲突，
使用者无从判断以哪个为准。按本站收录标准不予收录——这正是「关于」页新增那一段
所说的情形：条款自拟、与所称许可冲突的，只记进报告。

其中「urgent support（加急支持）」属服务收费，本身不影响授权；有问题的只是预算门槛
这一条。作者若明确该门槛只是自愿联系的请求而非使用条件，可重新评估。

注：Silver 的致谢列出 PixelMPlus（itouhiro）与 DOSGothic（leedheo）为主要贡献者，
这两款本站均已收录。
