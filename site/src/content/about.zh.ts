/** Chinese body text for the about page. The English version, about.en.ts, is produced by the Opus/Sonnet translation pipeline. */

export interface AboutSection {
  id: string;
  heading: string;
  paragraphs: string[];
  code?: string;
}

export const aboutIntro =
  '开源像素字体馆把散落在各处的自由许可点阵字体收进同一间标本馆：拆开到每个字形，用同一把尺子量，数清每张字表的覆盖，再给你一个能随手打字的试写框。字体属于它们各自的作者；这里做的只是整理与陈列。';

export const aboutSections: AboutSection[] = [
  {
    id: 'criteria',
    heading: '收录标准',
    paragraphs: [
      '只收录自由许可字体，判定从严：授权必须明确允许任何人使用、复制、修改、再分发并允许商用，且明确适用于本站收录的这份文件，来源链可核验。仅写着“免费”“免费商用”“freeware”、只允许复制，或“将来会改成开源许可”的，都不算。因此站上每一款字体都可放心商用。',
      '写着“作者声明”“个人使用条款”这类自拟授权的，多半收不进来。能不能收不看条款叫什么名字，只看内容是否满足自由软件与自由字体的通行定义：任何人可为任何目的使用、研究、修改与再分发，不因用途或使用者身份设限，授权不可事后单方撤回，并随衍生版本传递。缺任何一条，只记进收录报告，不上架。',
      '收录不限文种，中日韩与拉丁文字的字体都收。点阵格式之间（BDF、PCF、OTB、kbitx等）可无损互转，收录时一视同仁。分界在于字体本身是不是点阵：只发布矢量像素轮廓（TTF/OTF）的，会按其原生格点栅格化转回点阵，并在页面标注“转制”与推导方式。',
      '每款字体的详情页都注明收录来源。发现收录错误或希望移除，请在仓库提issue。',
    ],
  },
  {
    id: 'metrics',
    heading: '度量口径',
    paragraphs: [
      '宣称大小取自字体声明（PIXEL_SIZE、SIZE或FONTBOUNDINGBOX），即设计格点的高度。',
      '汉字墨迹字面是实际点亮像素的测量值：取该字体覆盖的《通用规范汉字表》一级字（不足100字时退化为全部统一表意文字），逐字形计算点亮像素的外接框，宽高分别取中位数。一款“16px”字体的汉字通常实际占15×15或14×15，这个数字比宣称大小更能说明字体的视觉尺寸。无汉字的字体改报大写字高与x字高。',
      '最大墨迹范围是全部字形中最大的点亮范围。组合符号或超宽私用区字形可能超出宣称框，属正常现象。',
    ],
  },
  {
    id: 'coverage',
    heading: '覆盖率口径',
    paragraphs: [
      '覆盖率按码位统计：字体编码表中的每个码位计一次，分母来自仓库内版本化的字表数据文件，每张字表的来源与版本注于文件头，悬停表名可见。',
      'Unicode区段的分母采用Unicode 17.0已指派码位（不含代理区，含私用区），因此与使用旧版Unicode分母的工具相比数字可能略有出入。',
      '兼容表意文字单独统计；其中12个码位按Unicode官方注记实为统一表意文字，已在总览中脚注标明。',
      'GB 18030-2022的三个实现级别按标准第9章的汉字及部首口径构造（27584 / 27780 / 88115字），构造依据与引文见仓库docs/research/。',
    ],
  },
  {
    id: 'rendering',
    heading: '样例渲染说明',
    paragraphs: [
      '所有样例由浏览器canvas逐像素绘制，每个点永远是锐利的正方形，不经过操作系统字体渲染，因此在任何平台上看到的效果一致，也就是字体真实的样子。',
      '排版为简单的从左到右逐字排布：不做shaping、不做kerning、不支持竖排。缺字以红底虚线占位框标出。',
    ],
  },
  {
    id: 'contribute',
    heading: '添加字体',
    paragraphs: [
      '把BDF或PCF文件（可以是 .gz压缩）放进fonts/ 下的一个新目录，运行构建即可收录。目录内可放family.toml补充人工资料，不放也能构建，站点会标“未整理”：',
    ],
    code: `fonts/my-font/
  my-font-16.bdf
  OFL.txt
  family.toml    # 可选，示例：

name = "My Font"
name_zh = "我的字体"
authors = ["作者名"]
homepage = "https://example.com"
description = "一句话介绍"
form = "gothic"          # 字形分类：gothic|mingcho|rounded|kai|fangsong|…
vibes = ["retro-game"]   # 气质标签，自由填写
aliases = ["曾用名"]     # 可选：曾用名／别名，只用于搜索`,
  },
  {
    id: 'disclaimer',
    heading: '免责声明',
    paragraphs: [
      '许可证信息由构建器自动识别或人工登记，仅供参考；实际授权以各字体上游发布的许可证原文为准。商用前请自行核对。',
      '本站的收录判定只针对著作权授权。有些字体名含第三方注册商标（如IBM VGA、Adobe Helvetica），这是指明字形来源的指称性使用；本站照原名收录，不代表商标权利人的背书或关联。',
      '字表数据的第三方来源与授权见仓库THIRD_PARTY_NOTICES.md。',
    ],
  },
];

export const aboutDataSourcesHeading = '字表数据来源';
export const aboutDataSourcesIntro =
  '以下字表驱动覆盖率统计，逐表注明数据来源；完整引用与授权见仓库。';
