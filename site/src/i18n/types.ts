/** Type definitions for the site-wide UI strings.
 *
 * zh.ts is the source text; en.ts is produced by the translation workflow;
 * Traditional is converted from zh via OpenCC (see hant.ts) and has no
 * separately maintained text.
 */

export type Lang = 'zh' | 'zh-Hant' | 'en' | 'ja' | 'ko' | 'fr';

export interface UIStrings {
  siteName: string;
  siteTagline: string;
  /** Label for the language-menu button, e.g. "语言"/"Language" — not the current language's own name for itself. */
  /** Link letting keyboard users skip past the header straight to the main content */
  skipToContent: string;
  /** Accessible name for the header nav */
  siteNavLabel: string;
  langLabel: string;
  themeToggle: string;

  nav: {
    catalogue: string;
    about: string;
    github: string;
    tools: string;
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
    results: string; // {n} placeholder
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
  /** Vibe/mood tags: the data stores slugs, and display needs localization */
  vibeNames: Record<string, string>;
  /** Display names for widths (Condensed and the like) */
  widthNames: Record<string, string>;
  scriptNames: Record<string, string>;
  /** Detection rules for each writing system, shown as the chip's hover tooltip */
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
    /** Accessible name for the generic "close" button */
    close: string;
    backToCatalogue: string;
    /** Title for the variant-sizes overview table */
    sizesOverview: string;
    variants: string;
    sampleTitle: string;
    presets: string;
    missingCount: string; // {n}
    metricsTitle: string;
    claimedSize: string;
    hanInk: string;
    hanInkNone: string;
    /** Recommended display size as noted in upstream documentation */
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
    /** Accessible name for the footer nav */
    navLabel: string;
    /** License for the site itself (code and collection data). The copyright line is language-independent and hardcoded in the footer markup */
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
  tools: {
    title: string;
    intro: string;
    cards: { slug: string; name: string; blurb: string }[];
  };
}
