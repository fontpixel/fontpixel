import { describe, expect, test } from 'vitest';
import { VIBE_GROUPS, vibeNames, vibeGroupName } from './vibes';
import { readFileSync } from 'node:fs';

describe('curated Vibes', () => {
  const audit = JSON.parse(readFileSync(new URL('../../../docs/audits/vibes-audit-2026-09-17.json', import.meta.url), 'utf8'));
  const tags = VIBE_GROUPS.flatMap(group => group.tags);

  test('every catalogue tag belongs to exactly one translated group', () => {
    expect(new Set(tags).size).toBe(tags.length);
    for (const lang of ['en', 'zh', 'zh-Hant', 'ja', 'ko', 'fr']) {
      const names = vibeNames(lang);
      for (const family of Object.values(audit) as { vibes: string[] }[]) {
        expect(family.vibes.length).toBeGreaterThan(0);
        for (const tag of family.vibes) {
          expect(tags).toContain(tag);
          expect(names[tag]?.length).toBeGreaterThan(0);
        }
      }
      for (const group of VIBE_GROUPS) expect(vibeGroupName(group, lang).length).toBeGreaterThan(0);
    }
  });
});
