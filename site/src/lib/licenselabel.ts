/** 许可证的短标签：筛选面板上的 chip 用，中英文一致。
 *
 * 完整名称（已 i18n）在每个字体详情页的 License 一栏里，chip 只需要一个
 * 认得出的通用缩写。SPDX id 本身多半已经够短，只有少数需要修饰。
 */
const OVERRIDES: Record<string, string> = {
  'CC-BY-SA-4.0': 'CC BY-SA 4.0',
  'LicenseRef-ISAS-1988': 'ISAS (1988)',
  'LicenseRef-Mplus': 'M+ Fonts',
  'LicenseRef-PublicDomain': 'Public Domain',
  'LicenseRef-UW-ttyp0': 'UW ttyp0',
};

export function licenseShortLabel(spdx: string): string {
  const hit = OVERRIDES[spdx];
  if (hit) return hit;
  // 未收录的 LicenseRef-* 至少去掉前缀，别把内部 id 直接示人
  return spdx.startsWith('LicenseRef-')
    ? spdx.slice('LicenseRef-'.length)
    : spdx;
}
