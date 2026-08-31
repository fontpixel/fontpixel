"""默认样例句(spec §5.2)与核心包字符集。"""

from __future__ import annotations

SAMPLES: dict[str, str] = {
    "latin": "Sphinx of black quartz, judge my vow. 0123456789",
    "latin-supp": "Naïve déjà forêt gâteau très Noël île goût ça · Größe Bäcker Öl Übung · niño ¿qué? Ávila canción Perú · ação avô limões Luís · città così però più · Ærø smörgås ský",
    "latin-ext": "Pchnąć w tę łódź jeża lub ośm skrzyń fig · Příliš žluťoučký kůň úpěl ďábelské ódy · árvíztűrő tükörfúrógép · çığır şeker İstanbul · ābece ēdiens jūra mīļš · œuvre",
    "zh-Hans": "天地玄黄，宇宙洪荒。日月盈昃，辰宿列张。",
    "zh-Hant": "落霞與孤鶩齊飛，秋水共長天一色。",
    "ja": "色は匂へど 散りぬるを 我が世誰ぞ 常ならむ",
    "ko": "다람쥐 헌 쳇바퀴에 타고파",
    "cyrillic": "Съешь же ещё этих мягких французских булок, да выпей чаю.",
    "greek": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία.",
    "javascript": '// Quick sort: O(n log n) average, ASCII 0-9\nconst quickSort = ([p, ...rest]) =>\n  p === undefined\n    ? []\n    : [...quickSort(rest.filter((x) => x < p)), p,\n       ...quickSort(rest.filter((x) => x >= p))];\nconsole.log(quickSort([42, 7, 19, 3, 88, 0]), "OK!");',
    "box-drawing": "┌─┬─┐ ┏━┳━┓ ╔═╦═╗ ╭─┬─╮\n├─┼─┤ ┣━╋━┫ ╠═╬═╣ ├─┼─┤\n└─┴─┘ ┗━┻━┛ ╚═╩═╝ ╰─┴─╯\n┄┅┆┇┈┉┊┋ ╌╍╎╏ ╱╲╳ ╴╵╶╷ ╸╹╺╻",
}


def core_text() -> str:
    """核心包字符：可打印 ASCII + 平/片假名 + 谚文兼容字母 + 全部默认样例句。"""
    parts = [
        "".join(chr(c) for c in range(0x20, 0x7F)),
        "".join(chr(c) for c in range(0x3041, 0x3097)),
        "".join(chr(c) for c in range(0x30A1, 0x30FB)),
        "".join(chr(c) for c in range(0x3131, 0x318F)),
        *SAMPLES.values(),
    ]
    return "".join(parts)


CORE_TEXT = core_text()


def specimen(cps: list[int] | set[int], n: int = 24) -> str:
    """从字体自己的字形里取一段样例。

    图标／符号字体一个书写系统都不达标，会落到拉丁兜底，于是拿英文句子去排
    一个没有字母的字体，整行都是缺字框。这时改用字体自身的字形做样例。
    在全部码位上等距取样，而不是取头几个——头部往往是控制符或占位符。
    """
    usable = sorted(c for c in cps if c >= 0x20 and not 0x7F <= c <= 0x9F)
    if not usable:
        return ""
    if len(usable) <= n:
        picked = usable
    else:
        step = len(usable) / n
        picked = [usable[int(i * step)] for i in range(n)]
    return "".join(chr(c) for c in picked)


def sample_is_broken(text: str, cps: set[int], threshold: float = 0.5) -> bool:
    """样例里缺掉的字符是否已多到不适合再用（空格不计）。"""
    chars = [ch for ch in text if ch not in " \n"]
    if not chars:
        return True
    missing = sum(1 for ch in chars if ord(ch) not in cps)
    return missing >= threshold * len(chars)
