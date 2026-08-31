/** 全站 UI 文案的类型定义。
 *
 * zh.ts 为源文本；en.ts 由翻译流程产出；繁体由 zh 经 OpenCC 转换（见 hant.ts），
 * 不单独维护文本。
 */

export type Lang = 'zh' | 'zh-Hant' | 'en' | 'ja' | 'ko' | 'fr';

export interface UIStrings {
  siteName: string;
  siteTagline: string;
  /** 语言菜单按钮的标签，如「语言」/「Language」——不是当前语言的自称。 */
  /** 键盘用户绕过页头直达正文的链接 */
  skipToContent: string;
  /** 页头导航的可及名称 */
  siteNavLabel: string;
  langLabel: string;
  themeToggle: string;

  nav: {
    catalogue: string;
    about: string;
    github: string;
  };

  catalogue: {
    searchPlaceholder: string;
    samplePlaceholder: string;
    sampleLabel: string;
    zoom: string;
    invert: string;
    grid: string;
    nowrap: string;
    boxDrawing: string;
    frameNone: string;
    frameCode: string;
    frameGame: string;
    results: string; // {n} 占位
    noResults: string;
    noResultsHint: string;
    sort: string;
    sortName: string;
    sortSize: string;
    sortGlyphs: string;
    filters: string;
    reset: string;
    form: string;
    vibes: string;
    sizes: string;
    inkHeight: string;
    scripts: string;
    license: string;
    spacing: string;
    weights: string;
    coverageAny: string;
    coveragePresets: string;
    charsLookup: string;
    charsPlaceholder: string;
    charsHint: string;
  };

  forms: Record<string, string>;
  /** 气质标签：数据里存的是 slug，展示需本地化 */
  vibeNames: Record<string, string>;
  /** 字宽（Condensed 之类）显示名 */
  widthNames: Record<string, string>;
  scriptNames: Record<string, string>;
  /** 每种书写系统的判定规则，显示为 chip 的悬停说明 */
  scriptRules: Record<string, string>;
  weightNames: Record<string, string>;
  spacingNames: Record<string, string>;

  card: {
    glyphs: string;
    uncurated: string;
    converted: string;
    px: string;
    licenseUnknown: string;
  };

  detail: {
    /** 通用「关闭」按钮的可及名称 */
    close: string;
    backToCatalogue: string;
    /** 变体尺寸一览表的标题 */
    sizesOverview: string;
    variants: string;
    sampleTitle: string;
    presets: string;
    missingCount: string; // {n}
    metricsTitle: string;
    claimedSize: string;
    hanInk: string;
    hanInkNone: string;
    /** 上游文档标注的推荐显示尺寸 */
    displaySize: string;
    copyDots: string;
    copied: string;
    capHeight: string;
    xHeight: string;
    maxInk: string;
    maxInkNote: string;
    ascentDescent: string;
    bbox: string;
    monospaced: string;
    proportional: string;
    dwidthHist: string;
    inkDiagramTitle: string;
    inkDiagramClaimed: string;
    inkDiagramHan: string;
    inkDiagramMax: string;
    coverageTitle: string;
    downloadsTitle: string;
    downloadBdf: string;
    downloadPcf: string;
    downloadTtf: string;
    downloadTtfNote: string;
    downloadTtfSquare: string;
    downloadTtfRound: string;
    downloadVectorNote: string;
    buildNotes: string;
    downloadZip: string;
    downloadNote: string;
    fileSize: string;
    author: string;
    homepage: string;
    repository: string;
    provenance: string;
    licenseTitle: string;
    licenseViewFull: string;
    licenseDisclaimer: string;
    warningsTitle: string;
    glyphGridTitle: string;
    glyphGridBlocks: string;
    glyphGridSearch: string;
    glyphGridJump: string;
    inspectorCp: string;
    inspectorName: string;
    inspectorAdvance: string;
    inspectorBbx: string;
    inspectorInk: string;
    glyphCount: string;
  };

  coverage: {
    sections: Record<string, string>;
    overviewTitle: string;
    totalEncoded: string;
    planes: string;
    pua: string;
    hanTotal: string;
    compat: string;
    compatNote: string;
    unicodeBlocks: string;
    showAllBlocks: string;
    hideZeroBlocks: string;
    expandMissing: string;
    close: string;
    missingChars: string;
    complete: string;
    sourceLabel: string;
  };

  about: {
    title: string;
  };

  footer: {
    /** 页脚导航的可及名称 */
    navLabel: string;
    /** 本站自身（代码与馆藏数据）的许可。版权行是语言无关的，直接写在页脚标记里 */
    siteLicense: string;
    disclaimer: string;
    dataSources: string;
    sourceCode: string;
  };

  notFound: {
    title: string;
    hint: string;
    back: string;
  };
}
