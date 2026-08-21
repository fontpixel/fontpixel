/** 关于页中文正文。英文版 about.en.ts 由 Opus/Sonnet 翻译流程产出。 */

export interface AboutSection {
  id: string;
  heading: string;
  paragraphs: string[];
  code?: string;
}

export const aboutIntro =
  '点阵字库把散落在各处的开源点阵字体收进同一间标本馆：拆开到每个字形，用同一把尺子量，数清每张字表的覆盖，再给你一个能随手打字的试写框。字体属于它们各自的作者；这里做的只是整理与陈列。';

export const aboutSections: AboutSection[] = [
  {
    id: 'criteria',
    heading: '收录标准',
    paragraphs: [
      '只收录允许再分发的开源或自由许可字体，以 CJK 点阵字体为主。原生点阵格式（BDF、PCF，以及可无损转换的 OTB、kbitx 等）优先；部分字体作者只发布了矢量化的像素轮廓字体(TTF/OTF)，这类会按原生格点栅格化转回点阵，并在页面上标注「转制」与推导方式。',
      '每款字体的详情页都注明收录来源。发现收录错误或希望移除，请在仓库提 issue。',
    ],
  },
  {
    id: 'metrics',
    heading: '度量口径',
    paragraphs: [
      '宣称大小取自字体声明(PIXEL_SIZE、SIZE 或 FONTBOUNDINGBOX)，即设计格点的高度。',
      '汉字墨迹字面是实际点亮像素的测量值：取该字体覆盖的《通用规范汉字表》一级字（不足 100 字时退化为全部统一表意文字），逐字形计算点亮像素的外接框，宽高分别取中位数。一款「16px」字体的汉字通常实际占 15×15 或 14×15，这个数字比宣称大小更能说明字体的视觉尺寸。无汉字的字体改报大写字高与 x 字高。',
      '最大墨迹范围是全部字形中最大的点亮范围。组合符号或超宽私用区字形可能超出宣称框，属正常现象。',
    ],
  },
  {
    id: 'coverage',
    heading: '覆盖率口径',
    paragraphs: [
      '覆盖率按码位统计：字体编码表中的每个码位计一次，分母来自仓库内版本化的字表数据文件，每张字表的来源与版本注于文件头，悬停表名可见。',
      'Unicode 区段的分母采用 Unicode 17.0 已指派码位（不含代理区，含私用区），因此与使用旧版 Unicode 分母的工具相比数字可能略有出入。',
      '兼容表意文字单独统计；其中 12 个码位(FA0E、FA0F、FA11、FA13、FA14、FA1F、FA21、FA23、FA24、FA27、FA28、FA29)按 Unicode 官方注记实为统一表意文字，已在总览中脚注标明。',
      'GB 18030-2022 的三个实现级别按标准第 9 章的汉字及部首口径构造（27584 / 27780 / 88115 字），构造依据与引文见仓库 docs/research/。',
    ],
  },
  {
    id: 'rendering',
    heading: '样例渲染说明',
    paragraphs: [
      '所有样例由浏览器 canvas 逐像素绘制，每个点永远是锐利的正方形，不经过操作系统字体渲染，因此在任何平台上看到的效果一致，也就是字体真实的样子。',
      '排版为简单的从左到右逐字排布：不做 shaping、不做 kerning、不支持竖排。缺字以虚线占位框表示，可开启缺字高亮。',
    ],
  },
  {
    id: 'contribute',
    heading: '添加字体',
    paragraphs: [
      '把 BDF 或 PCF 文件（可以是 .gz 压缩）放进 fonts/ 下的一个新目录，运行构建即可收录。目录内可放 family.toml 补充人工资料，不放也能构建，站点会标「未整理」：',
    ],
    code: `fonts/my-font/
  my-font-16.bdf
  OFL.txt
  family.toml    # 可选，示例：

name = "My Font"
name_zh = "我的字体"
author = "作者名"
homepage = "https://example.com"
description = "一句话介绍"
form = "gothic"          # 字形分类：gothic|mingcho|rounded|kai|fangsong|…
vibes = ["retro-game"]   # 气质标签，自由填写`,
  },
  {
    id: 'disclaimer',
    heading: '免责声明',
    paragraphs: [
      '许可证信息由构建器自动识别或人工登记，仅供参考；实际授权以各字体上游发布的许可证原文为准。商用前请自行核对。',
      '字表数据的第三方来源与授权见仓库 THIRD_PARTY_NOTICES.md。',
    ],
  },
];

export const aboutDataSourcesHeading = '字表数据来源';
export const aboutDataSourcesIntro =
  '以下字表驱动覆盖率统计，逐表注明数据来源；完整引用与授权见仓库。';
