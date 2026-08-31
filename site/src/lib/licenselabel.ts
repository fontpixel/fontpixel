/** Short license labels, used for chips in the filter panel; same in Chinese and English.
 *
 * The full (i18n'd) name lives in the License field on each font's detail
 * page — the chip just needs a recognizable common abbreviation. Most SPDX
 * ids are already short enough as-is; only a few need adjusting.
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
  // For LicenseRef-* not in the map, at least strip the prefix so we don't show the raw internal id to the user
  return spdx.startsWith('LicenseRef-')
    ? spdx.slice('LicenseRef-'.length)
    : spdx;
}
