import { expect, test } from 'vitest';
import { licenseShortLabel } from './licenselabel';

test('每个收录中的许可证都有通用缩写', () => {
  expect(
    Object.fromEntries(
      [
        'BSD-2-Clause',
        'CC-BY-SA-4.0',
        'GPL-2.0-only',
        'GPL-3.0-or-later',
        'HPND',
        'LicenseRef-Baekmuk',
        'LicenseRef-ISAS-1988',
        'LicenseRef-Mplus',
        'LicenseRef-PublicDomain',
        'LicenseRef-Tamsyn',
        'LicenseRef-UW-ttyp0',
        'MIT',
        'OFL-1.1',
        'Unlicense',
        'WTFPL',
      ].map((id) => [id, licenseShortLabel(id)]),
    ),
  ).toEqual({
    'BSD-2-Clause': 'BSD-2-Clause',
    'CC-BY-SA-4.0': 'CC BY-SA 4.0',
    'GPL-2.0-only': 'GPL-2.0-only',
    'GPL-3.0-or-later': 'GPL-3.0-or-later',
    HPND: 'HPND',
    'LicenseRef-Baekmuk': 'Baekmuk',
    'LicenseRef-ISAS-1988': 'ISAS (1988)',
    'LicenseRef-Mplus': 'M+ Fonts',
    'LicenseRef-PublicDomain': 'Public Domain',
    'LicenseRef-Tamsyn': 'Tamsyn',
    'LicenseRef-UW-ttyp0': 'UW ttyp0',
    MIT: 'MIT',
    'OFL-1.1': 'OFL-1.1',
    Unlicense: 'Unlicense',
    WTFPL: 'WTFPL',
  });
});

test('未收录的 LicenseRef-* 至少剥掉前缀', () => {
  expect(licenseShortLabel('LicenseRef-SomethingNew')).toBe('SomethingNew');
});
