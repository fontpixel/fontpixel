import { expect, test } from 'vitest';
import { SITE_VERSION } from './version';

test('site version', () => {
  expect(SITE_VERSION).toBe(1);
});
