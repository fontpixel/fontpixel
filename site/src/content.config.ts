import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

/** 工具与文档内容（bdfparser、BDF 规格、字体模板等），源自 font.tomchen.org 并入。
 *
 * 正文目前为英文单语；与家族元数据同一条规则——将来补中文时按 `*.zh.mdx`
 * 放同名文件，其余语言回落英文。id 即「区块/路径」，如 bdf-spec/intro。
 */
const docs = defineCollection({
  loader: glob({
    pattern: '**/*.{md,mdx}',
    base: './src/content/docs',
    // 默认的 slugify 会吃掉点号（spec_2.1 → spec_21），按原路径保留 id
    generateId: ({ entry }) => entry.replace(/\.(md|mdx)$/, ''),
  }),
  schema: z.object({
    title: z.string(),
    /** 侧栏短标签；缺省用 title */
    label: z.string().optional(),
    /** 侧栏排序，小者在前 */
    order: z.number().default(0),
    description: z.string().optional(),
  }),
});

export const collections = { docs };
