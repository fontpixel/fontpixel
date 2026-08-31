/* eslint-disable */
// 由 port_docs2.py 从原站 MDX 的 <BDF func={…}> 用法生成；改动演示请改这里。
/** 单个活演示：fn 收到已加载的 Font 与 bdfparser 各类的集合。 */
export interface BdfDemo {
  fn: (font: any, ctx: any) => any;
  fontfile?: string;
  size?: number;
  pixelcolors?: Record<number, string | null>;
}

export const DEMOS: Record<string, BdfDemo> = {
  'js-index-0': {
    fn: (font) => {
    const ac = font
      .glyph('a')
      .draw()
      .crop(6, 8, 1, 2)
      .concat(font.glyph('c').draw().crop(6, 8, 1, 2))
      .shadow()
    const ac_8x8 = ac.enlarge(8, 8)
    return ac_8x8
  },
    size: 1,
  },
  'js-index-1': {
    fn: (font) => {
    return font.draw('Hello!', {direction: 'rl'}).glow()
  },
  },
  'js-font-0': {
    fn: (font) => {
    return font.glyph('a').draw()
  },
  },
  'js-font-1': {
    fn: (font) => {
    return font.glyphbycp(97).draw()
  },
  },
  'js-font-2': {
    fn: (font) => font.draw('Bdf Hi'),
  },
  'js-font-3': {
    fn: (font) => font.draw('Bdf Hi', { mode: 0 }),
  },
  'js-font-4': {
    fn: (font) => font.draw('مرحبا', { direction: 'rl' }),
  },
  'js-font-5': {
    fn: (font) => font.draw('Bdf Hi', { linelimit: 30 }),
  },
  'js-font-6': {
    fn: (font) => font.draw('Bé H好Δi的', {
  missing: { glyphname: 'missing glyph', codepoint: 0, bbw: 16, bbh: 16, bbxoff: 0, bbyoff: -2, swx0: 1000, swy0: 0, dwx0: 16, dwy0: 0, swx1: null, swy1: null, dwx1: null, dwy1: null, vvectorx: null, vvectory: null, hexdata: [ '0000', '0000', '0000', '3ff8', '3018', '2828', '2448', '2288', '2108', '2288', '2448', '2828', '3018', '3ff8', '0000', '0000' ] },
}),
    fontfile: 'unifont-13.0.04-for-test.bdf',
  },
  'js-font-7': {
    fn: (font) => font.drawcps([66, 100, 102, 32, 72, 105]),
  },
  'js-glyph-0': {
    fn: (font) => font.glyph("'").draw(),
    fontfile: 'spec_example_fixed.bdf',
  },
  'js-glyph-1': {
    fn: (font) => font.glyph("'").draw(1),
    fontfile: 'spec_example_fixed.bdf',
  },
  'js-glyph-2': {
    fn: (font) => font.glyph("'").draw(2),
    fontfile: 'spec_example_fixed.bdf',
  },
  'js-glyph-3': {
    fn: (font) => font.glyph("'").draw(-1, [6, 17, 1, 1]),
    fontfile: 'spec_example_fixed.bdf',
  },
  'js-bitmap-0': {
    fn: (font, {$Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright
  },
  },
  'js-bitmap-1': {
    fn: (font, {$Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright.crop(7, 4, -1, 1)
  },
  },
  'js-bitmap-2': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    const bitmap_quoteright2 = $Bitmap([
      '01110',
      '02110',
      '01102',
      '10200',
      '01000',
    ])
    const bitmap_j = font.glyph('j').draw(2)
    return Bitmap.concatall([bitmap_quoteright, bitmap_j, bitmap_quoteright2])
  },
  },
  'js-bitmap-3': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    const bitmap_quoteright2 = $Bitmap([
      '01110',
      '02110',
      '01102',
      '10200',
      '01000',
    ])
    const bitmap_j = font.glyph('j').draw(2)
    return Bitmap.concatall([bitmap_quoteright, bitmap_j, bitmap_quoteright2], {offsetlist: [-3, 4]})
  },
  },
  'js-bitmap-4': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    const bitmap_quoteright2 = $Bitmap([
      '01110',
      '02110',
      '01102',
      '10200',
      '01000',
    ])
    const bitmap_j = font.glyph('j').draw(2)
    return Bitmap.concatall([bitmap_quoteright, bitmap_j, bitmap_quoteright2], {direction: 0})
  },
  },
  'js-bitmap-5': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    const bitmap_quoteright2 = $Bitmap([
      '01110',
      '02110',
      '01102',
      '10200',
      '01000',
    ])
    const bitmap_j = font.glyph('j').draw(2)
    return Bitmap.concatall([bitmap_quoteright, bitmap_j, bitmap_quoteright2], {align: 0})
  },
  },
  'js-bitmap-6': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    const bitmap_quoteright2 = $Bitmap([
      '01110',
      '02110',
      '01102',
      '10200',
      '01000',
    ])
    const bitmap_j = font.glyph('j').draw(2)
    return Bitmap.concatall([bitmap_quoteright, bitmap_j, bitmap_quoteright2], {direction: 0, align: 0})
  },
  },
  'js-bitmap-7': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright
  },
  },
  'js-bitmap-8': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright.enlarge(3, 1)
  },
  },
  'js-bitmap-9': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright
  },
  },
  'js-bitmap-10': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright.shadow(2, -1)
  },
  },
  'js-bitmap-11': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright
  },
  },
  'js-bitmap-12': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright.glow()
  },
  },
  'js-bitmap-13': {
    fn: (font, {Bitmap, $Bitmap}) => {
    const bitmap_quoteright = $Bitmap([
      '01110000',
      '01110000',
      '01110000',
      '01100000',
      '11100000',
      '11000000',
    ])
    return bitmap_quoteright.glow(1)
  },
  },
};
