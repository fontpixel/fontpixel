/** 简体 → 繁体（台湾用字）转换。
 *
 * 繁体中文不是另一种语言，是同一种语言的另一套字形与词汇，所以走 OpenCC
 * 转换而不是翻译：改一句中文，繁体版自动跟着变，不存在两份文本不同步。
 *
 * 用 s2twp（台湾用字 + 词汇替换）而不是纯字形的 s2t——后者会留下「軟件」
 * 「信息」这类大陆词，读起来一眼就是机转的。代价是 s2twp 偶尔会在专业
 * 复合词上出错，用 FIXUPS 修正。
 *
 * 转换在构建期完成（本站是全静态的），并按唯一字符串缓存，全站一次构建
 * 约一千条、毫秒级。
 */
import * as OpenCC from 'opencc-js';

const convert = OpenCC.Converter({ from: 'cn', to: 'twp' });

/** s2twp 在这些词上判断有误，转换后修正。 */
const FIXUPS: [RegExp, string][] = [
  // s2twp 把「位图」当独立词转成「點陣圖」（bitmap image），但本站的「位图」
  // 无一例外指位图字体／strike，台湾称「點陣」。全站六处用法均已核对。
  [/點陣圖/g, '點陣'],
  // 台湾习惯说「授權」而非「許可證」
  [/許可證/g, '授權'],
  // 站名的繁体版是定名（見 sitenames.json 的 zh-Hant），不是逐字转换的产物；
  // 这条规则把嵌在任意句子里的站名也一并矫正（如关于页导语）。
  [/開源畫素字型館/g, '開源點陣字型館'],
  // 简体正文统一用弯引号“”，繁体（台湾）惯例是直角引号「」，转换时换回来。
  // 内层引号同理：‘’→『』。OpenCC 只管字与词，不动标点。
  [/‘([^’]*)’/g, '『$1』'],
  [/“([^”]*)”/g, '「$1」'],
];

/** 整句覆写：少数文案的繁体版是另写的，不是简体版转换来的。
 *
 * 例如站点描述——繁体读者搜的关键词组合与简体不同（「點陣」「畫素」「位元圖」
 * 并用），这类 SEO 取向的差异 OpenCC 变不出来，也不该用 FIXUPS 硬凑（那是逐词
 * 替换，会误伤别处）。键是简体原文，值是最终繁体文本。
 */
const OVERRIDES: Record<string, string> = {
  '免费可商用的自由开源点阵/像素/位图字体合集，BDF、PCF、TTF格式下载':
    '免費可商用的自由開源點陣/像素/畫素/位元圖字型合集，BDF、PCF、TTF格式下載',
};

const cache = new Map<string, string>();

/** 把一段简体中文转成繁体；非中文内容原样返回。 */
export function toHant(text: string): string {
  if (!text) return text;
  const hit = cache.get(text);
  if (hit !== undefined) return hit;
  const override = OVERRIDES[text];
  if (override !== undefined) {
    cache.set(text, override);
    return override;
  }
  let out = convert(text);
  for (const [re, to] of FIXUPS) out = out.replace(re, to);
  cache.set(text, out);
  return out;
}

/** 深度转换一个只含字符串与嵌套对象的结构（用于整份 UI 文案）。 */
export function toHantDeep<T>(value: T): T {
  if (typeof value === 'string') return toHant(value) as unknown as T;
  if (Array.isArray(value)) return value.map(toHantDeep) as unknown as T;
  if (value && typeof value === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(value)) out[k] = toHantDeep(v);
    return out as T;
  }
  return value;
}
