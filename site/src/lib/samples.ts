/** 默认样例句 —— 与 pipeline/opf/samples.py 保持同步(spec §5.2)。 */

export const SAMPLES: Record<string, string> = {
  latin: 'Sphinx of black quartz, judge my vow. 0123456789',
  'latin-supp': 'Naïve déjà forêt gâteau très Noël île goût ça · Größe Bäcker Öl Übung · niño ¿qué? Ávila canción Perú · ação avô limões Luís · città così però più · Ærø smörgås ský',
  'latin-ext': 'Pchnąć w tę łódź jeża lub ośm skrzyń fig · Příliš žluťoučký kůň úpěl ďábelské ódy · árvíztűrő tükörfúrógép · çığır şeker İstanbul · ābece ēdiens jūra mīļš · œuvre',
  'zh-Hans': '天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。',
  'zh-Hant': '落霞與孤鶩齊飛，秋水共長天一色。',
  ja: '色は匂へど 散りぬるを 我が世誰ぞ 常ならむ',
  ko: '다람쥐 헌 쳇바퀴에 타고파',
  cyrillic: 'Съешь же ещё этих мягких французских булок, да выпей чаю.',
  greek: 'Ξεσκεπάζω την ψυχοφθόρα βδελυγμία.',
  javascript:
    '// Quick sort: O(n log n) average, ASCII 0-9\nconst quickSort = ([p, ...rest]) =>\n  p === undefined\n    ? []\n    : [...quickSort(rest.filter((x) => x < p)), p,\n       ...quickSort(rest.filter((x) => x >= p))];\nconsole.log(quickSort([42, 7, 19, 3, 88, 0]), "OK!");',
  'box-drawing': '┌─┬─┐ ┏━┳━┓ ╔═╦═╗ ╭─┬─╮\n├─┼─┤ ┣━╋━┫ ╠═╬═╣ ├─┼─┤\n└─┴─┘ ┗━┻━┛ ╚═╩═╝ ╰─┴─╯\n┄┅┆┇┈┉┊┋ ╌╍╎╏ ╱╲╳ ╴╵╶╷ ╸╹╺╻',
};

/** 这些预设靠字符逐格对齐说明问题，折行会毁掉版面，选中时强制关掉折行。 */
export const NOWRAP_PRESETS: ReadonlySet<string> = new Set(['box-drawing']);

export function defaultSample(sampleLang: string): string {
  return SAMPLES[sampleLang] ?? SAMPLES['latin']!;
}
