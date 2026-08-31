"""Default sample text (spec §5.2) and the core pack character set."""

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
    # Arabic joins letters and the renderer does no shaping/RTL, so a sentence
    # would render wrong; an isolated-form alphabet is direction-agnostic and
    # right for inspecting glyph coverage (includes Persian and Urdu letters).
    "arabic": "ا ب ت ث ج ح خ د ذ ر ز س ش ص ض ط ظ ع غ ف ق ك ل م ن ه و ي\nپ چ ژ گ ک ی · ٹ ڈ ڑ ں ھ ہ ے\n٠ ١ ٢ ٣ ٤ ٥ ٦ ٧ ٨ ٩ · ۰ ۱ ۲ ۳ ۴ ۵ ۶ ۷ ۸ ۹",
    "javascript": '// Quick sort: O(n log n) average, ASCII 0-9\nconst quickSort = ([p, ...rest]) =>\n  p === undefined\n    ? []\n    : [...quickSort(rest.filter((x) => x < p)), p,\n       ...quickSort(rest.filter((x) => x >= p))];\nconsole.log(quickSort([42, 7, 19, 3, 88, 0]), "OK!");',
    "box-drawing": "┌─┬─┐ ┏━┳━┓ ╔═╦═╗ ╭─┬─╮\n├─┼─┤ ┣━╋━┫ ╠═╬═╣ ├─┼─┤\n└─┴─┘ ┗━┻━┛ ╚═╩═╝ ╰─┴─╯\n┄┅┆┇┈┉┊┋ ╌╍╎╏ ╱╲╳ ╴╵╶╷ ╸╹╺╻",
}


def core_text() -> str:
    """Core pack characters: printable ASCII + hiragana/katakana + Hangul compatibility jamo + every default sample sentence."""
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
    """Pull a sample from the font's own glyphs.

    Icon/symbol fonts don't reach threshold for any script, so they fall
    back to Latin — which means setting an English sentence in a font
    that has no letters, filling the whole line with missing-glyph boxes.
    In that case, use the font's own glyphs as the sample instead. Sample
    evenly across all codepoints rather than taking the first few — the
    front of the range is often control characters or placeholders.
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
    """Whether too many characters in the sample are missing to still be usable (spaces excluded)."""
    chars = [ch for ch in text if ch not in " \n"]
    if not chars:
        return True
    missing = sum(1 for ch in chars if ord(ch) not in cps)
    return missing >= threshold * len(chars)
