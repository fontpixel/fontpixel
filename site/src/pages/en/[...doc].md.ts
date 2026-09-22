import type { GetStaticPaths, APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { docPath, type DocEntry, type DocSection } from '../../lib/docs';

export const getStaticPaths: GetStaticPaths = async () => (await getCollection('docs')).map((entry) => {
  const section = entry.id.split('/')[0] as DocSection;
  return { params: { doc: `${docPath(section, entry).slice(1)}index` }, props: { entry } };
});

export const GET: APIRoute = ({ props }) => {
  const entry = props.entry as DocEntry;
  // Only omit this site's MDX component imports. Python and JavaScript imports
  // inside code examples are documentation and must remain intact.
  const body = (entry.body ?? '').replace(/^import[^\r\n]+from ['"]@dc\/[^'"\r\n]+['"];?[ \t]*\r?$/gm, '').trim();
  return new Response(`# ${entry.data.title}\n\n${entry.data.description}\n\n${body}\n`, {
    headers: { 'Content-Type': 'text/markdown; charset=utf-8' },
  });
};
