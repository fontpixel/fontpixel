import { readFileSync } from 'node:fs';
import { expect, test } from 'vitest';
import { DATA_SCHEMA_VERSION, DetailSchema, IndexSchema } from './schema';

function load(name: string): unknown {
  return JSON.parse(
    readFileSync(new URL(`./__fixtures__/${name}`, import.meta.url), 'utf-8'),
  );
}

test('pipeline index.json satisfies contract', () => {
  const parsed = IndexSchema.parse(load('index.fixture.json'));
  expect(parsed.schemaVersion).toBe(DATA_SCHEMA_VERSION);
  expect(parsed.families.length).toBe(2);
  const mini = parsed.families.find((f) => f.slug === 'mini')!;
  expect(mini.license.spdx).toBe('OFL-1.1');
  expect(mini.variants.length).toBe(2);
});

test('pipeline detail.json satisfies contract', () => {
  const parsed = DetailSchema.parse(load('detail.fixture.json'));
  expect(parsed.slug).toBe('mini');
  const firstVariant = parsed.meta.variants[0]!.id;
  expect(parsed.coverage[firstVariant]!['gb2312']![1]).toBe(6763);
});
