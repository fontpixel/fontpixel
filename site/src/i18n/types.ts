/** 全站 UI 文案的类型定义。zh.ts 为源文本；en.ts 由 Opus/Sonnet 翻译流程产出。 */

export type Lang = 'zh' | 'en';

export interface UIStrings {
  siteName: string;
  siteNameLatin: string;
  siteTagline: string;
  langLabel: string;
  langSwitch: string;
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
    results: string; // {n} 占位
    noResults: string;
    noResultsHint: string;
    sort: string;
    sortName: string;
    sortSize: string;
    sortGlyphs: string;
    sortAdded: string;
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
    origin: string;
    originAll: string;
    originNative: string;
    originConverted: string;
    coveragePresets: string;
    charsLookup: string;
    charsPlaceholder: string;
    charsHint: string;
  };

  forms: Record<string, string>;
  scriptNames: Record<string, string>;
  weightNames: Record<string, string>;
  spacingNames: Record<string, string>;

  card: {
    glyphs: string;
    uncurated: string;
    converted: string;
    px: string;
    commercialOk: string;
    licenseUnknown: string;
  };

  detail: {
    backToCatalogue: string;
    variants: string;
    sampleTitle: string;
    presets: string;
    highlightMissing: string;
    missingCount: string; // {n}
    metricsTitle: string;
    claimedSize: string;
    hanInk: string;
    hanInkNone: string;
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
    downloadZip: string;
    downloadNote: string;
    fileSize: string;
    author: string;
    homepage: string;
    repository: string;
    provenance: string;
    convertedFrom: string;
    licenseTitle: string;
    licenseViewFull: string;
    licenseConfidence: Record<string, string>;
    licenseCommercial: string;
    licenseNonCommercialUnknown: string;
    licenseDisclaimer: string;
    warningsTitle: string;
    glyphGridTitle: string;
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
    missingChars: string;
    complete: string;
    sourceLabel: string;
  };

  about: {
    title: string;
  };

  footer: {
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
