/** About page copy, English. Translated from about.zh.ts; keep the two in sync. */

import type { AboutSection } from './about.zh';

export const aboutIntro =
  'Open Pixel Fonts gathers freely licensed bitmap fonts from wherever they happen to live and files them in one specimen cabinet: parsed glyph by glyph, measured to one consistent standard, tallied for character coverage, and paired with previews you can type into. The fonts belong to the people who made them; all that happens here is cataloguing and display.';

export const aboutSections: AboutSection[] = [
  {
    id: 'criteria',
    heading: 'Inclusion criteria',
    paragraphs: [
      'Only freely licensed fonts make it in, and the bar is strict: the license must clearly allow anyone to use, copy, modify and redistribute the font, commercial use included, and it must verifiably cover the exact file catalogued here. “Free”, “free for commercial use”, “freeware”, copying-only terms, or a promise to “switch to an open-source license later” do not qualify. Everything on the site is therefore safe to use commercially.',
      'Fonts under bespoke terms such as an “author’s statement” or a “personal use license” rarely make it in. What matters is not what the terms are called but whether they meet the accepted definitions of free software and libre fonts: anyone may use, study, modify and redistribute for any purpose; no restriction may turn on the use or the user; the grant cannot be revoked after the fact; and it must carry over to derivatives. Miss any one of those and the font goes into the import report, not the catalogue.',
      'The collection is not limited to any one script; CJK and Latin faces are both welcome. Bitmap formats convert losslessly between one another - BDF, PCF, OTB, kbitx - so they are all treated alike. The line that matters is whether the font is a bitmap at all: where an author publishes only a vectorised pixel outline (TTF/OTF), it is rasterised back to a bitmap on its native grid and the page marks it as “converted”, with the derivation shown.',
      "Each font's detail page records its provenance. If you spot something included in error, or you would like a font taken down, please open an issue in the repository.",
    ],
  },
  {
    id: 'metrics',
    heading: 'How metrics are measured',
    paragraphs: [
      "Nominal size comes from the font's own declaration (PIXEL_SIZE, SIZE, or FONTBOUNDINGBOX), which is the height of the design pixel grid.",
      'The Han ink box is measured from the pixels that are actually lit. The build takes the Level 1 characters of the Table of General Standard Chinese Characters that the font covers (falling back to all unified ideographs when fewer than 100 are present), computes the bounding box of the lit pixels for each glyph, and reports the median width and the median height. A “16px” font usually draws its Han characters at 15×15 or 14×15, which tells you more about the visual size of the face than the nominal figure does. Fonts without Han glyphs report cap height and x-height instead.',
      'Max ink extents is the largest lit area found across all glyphs. Combining marks and extra-wide Private Use Area glyphs may extend beyond the nominal box; that is normal.',
    ],
  },
  {
    id: 'coverage',
    heading: 'How coverage is counted',
    paragraphs: [
      "Coverage is counted by code point: every code point in the font's encoding table counts once. Denominators come from versioned character set data files kept in the repository; each file carries its source and version in its header, which you can see by hovering over the set name.",
      'Denominators for Unicode blocks use the code points assigned in Unicode 17.0, excluding surrogates and including the Private Use Areas. Figures may therefore differ slightly from tools that count against an older version of Unicode.',
      'Compatibility ideographs are counted separately; twelve of those code points are, per Unicode’s own annotations, actually unified ideographs, and the overview footnotes them.',
      'The three implementation levels of GB 18030-2022 are constructed from the Han character and radical definitions in Clause 9 of the standard, giving 27,584 / 27,780 / 88,115 characters. The reasoning and the quoted passages are in docs/research/ in the repository.',
    ],
  },
  {
    id: 'rendering',
    heading: 'How the previews are rendered',
    paragraphs: [
      "Every preview is drawn pixel by pixel on a browser canvas. Each dot is always a crisp square, and nothing goes through the operating system's font rasterizer, so what you see is the same on every platform: the font as it truly is.",
      'Layout is a plain left-to-right run of glyphs, with no shaping, no kerning, and no vertical writing. Missing characters are marked with red-tinted dotted placeholder boxes.',
    ],
  },
  {
    id: 'contribute',
    heading: 'Adding a font',
    paragraphs: [
      'Put the BDF or PCF files (.gz-compressed is fine) into a new directory under fonts/ and run the build. A family.toml in that directory adds the hand-entered details; it is optional, and a family without one still builds, marked “Uncurated” on the site:',
    ],
    code: `fonts/my-font/
  my-font-16.bdf
  OFL.txt
  family.toml    # optional, for example:

name = "My Font"
name_zh = "我的字体"
authors = ["Author name"]
homepage = "https://example.com"
description = "One-line description"
form = "gothic"          # category: gothic|mingcho|rounded|kai|fangsong|…
vibes = ["retro-game"]   # vibe tags, free-form
aliases = ["Former Name"] # optional former names / aliases, used for search only`,
  },
  {
    id: 'disclaimer',
    heading: 'Disclaimer',
    paragraphs: [
      'License information is either detected automatically by the builder or entered by hand, and is offered for reference only. What actually governs a font is the license text its author publishes upstream. Check it yourself before any commercial use.',
      'Inclusion here is judged on copyright licensing alone. Some font names contain third-party registered trademarks (IBM VGA or Adobe Helvetica, say) — nominative use that identifies where the glyphs come from. They are catalogued under their real names, implying no endorsement by or affiliation with any trademark owner.',
      'Third-party sources and licensing for the character set data are listed in THIRD_PARTY_NOTICES.md in the repository.',
    ],
  },
];

export const aboutDataSourcesHeading = 'Character set data sources';
export const aboutDataSourcesIntro =
  'The character sets below drive the coverage figures, each with its data source noted. Full citations and licensing are in the repository.';
