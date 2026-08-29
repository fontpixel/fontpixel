/** 默认样例句 —— 与 pipeline/fbf/samples.py 保持同步(spec §5.2)。 */

export const SAMPLES: Record<string, string> = {
  'zh-Hans': '天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。',
  'zh-Hant': '落霞與孤鶩齊飛，秋水共長天一色。',
  ja: '色は匂へど 散りぬるを 我が世誰ぞ 常ならむ',
  ko: '다람쥐 헌 쳇바퀴에 타고파',
  latin: 'Sphinx of black quartz, judge my vow. 0123456789',
};

export function defaultSample(sampleLang: string): string {
  return SAMPLES[sampleLang] ?? SAMPLES['latin']!;
}
