/** 工具与文档区块的路由与侧栏辅助。
 *
 * 路由形制：/{lang}/<section>/<slug>/，slug 为空即区块首页。
 * 内容为英文单语，六种语言路由都渲染同一份正文（页头等站壳仍随语言），
 * 与家族元数据「缺译回落」同一条规则。
 */
import { getCollection, type CollectionEntry } from 'astro:content';
import { LANGS } from '../i18n';

export type DocEntry = CollectionEntry<'docs'>;

export const DOC_SECTIONS = {
  'font-template': 'Font Template',
  'bdf-spec': 'BDF Specification',
  'bdfparser-js': 'bdfparser (JS/TS)',
  'bdfparser-py': 'bdfparser (Python)',
} as const;
export type DocSection = keyof typeof DOC_SECTIONS;

/** 区块内 slug：去掉区块前缀与结尾的 index。首页为空串。 */
export function docSlug(entry: DocEntry, section: DocSection): string {
  const rest = entry.id.slice(section.length + 1);
  return rest.replace(/(^|\/)index$/, '').replace(/\/$/, '');
}

/** 不含语言前缀的页面路径（Base 的 path 约定），带尾斜杠。 */
export function docPath(section: DocSection, entry: DocEntry): string {
  const slug = docSlug(entry, section);
  return `/${section}/` + (slug ? `${slug}/` : '');
}

export async function sectionEntries(section: DocSection): Promise<DocEntry[]> {
  const entries = await getCollection('docs', ({ id }) => id.startsWith(`${section}/`));
  return entries.sort((a, b) => a.data.order - b.data.order);
}

/** 四个区块共用的 getStaticPaths 实现。 */
export async function docStaticPaths(section: DocSection) {
  const entries = await sectionEntries(section);
  return LANGS.flatMap((lang) =>
    entries.map((entry) => ({
      params: { lang, slug: docSlug(entry, section) || undefined },
      props: { entry },
    })),
  );
}
