/** Owner's aesthetic preferences, added after the automatic coverage/size/license score.
 * Values are points, not percentages. Unlisted families receive no adjustment.
 * Keep exact family slugs here so translations, variants and related fonts do
 * not acquire a preference accidentally. Positive totals may exceed 100.
 */
export const RATING_ADJUSTMENTS: Readonly<Record<string, number>> = Object.freeze({
  'qiu-ye-yuan-ti-16': 0.5, // 秋叶圆体
  'zlabs-roundpix': 1, // Z工坊像素圆体
  'zlabs-pixel-12px': 1, // Z工坊像素黑体
  'poxiao-pixel': 1, // 破晓像素
  'muzai-pixel': 1, // 目哉像素
  'quan-pixel': 1, // 全小素
  'fusion-pixel': 1.5, // 缝合像素；不包括缝合粗像素
  'cubic-11': 1.5, // 俐方体11号
  'ark-pixel': 1.5, // 方舟像素 / Ark Pixel
  'boutique-bitmap': 1.5, // 精品点阵体
  'galmuri': 1.5,
  'misaki': 1.5,
});
