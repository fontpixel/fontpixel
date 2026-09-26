import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/** Tools and docs content (bdfparser, the BDF spec, font templates, etc.), merged in from font.tomchen.org.
 *
 * Body content is currently English-only; same rule as family metadata—when Chinese
 * is added later, place a same-named `*.zh.mdx` file, other languages fall back to English.
 * id is the "section/path", e.g. bdf_spec/intro.
 */
const docs = defineCollection({
  loader: glob({
    pattern: '**/*.{md,mdx}',
    base: './src/content/docs',
    // the default slugify would eat the dot (spec_2.1 -> spec_21); keep the original path as id
    generateId: ({ entry }) => entry.replace(/\.(md|mdx)$/, ''),
  }),
  schema: z.object({
    title: z.string(),
    /** short sidebar label; falls back to title if omitted */
    label: z.string().optional(),
    /** sidebar order, smaller sorts first */
    order: z.number().default(0),
    description: z.string().optional(),
  }),
});

export const collections = { docs };
