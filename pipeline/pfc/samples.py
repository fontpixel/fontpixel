"""默认样例句(spec §5.2)与核心包字符集。"""

from __future__ import annotations

SAMPLES: dict[str, str] = {
    "zh-Hans": "天地玄黄,宇宙洪荒。日月盈昃,辰宿列张。",
    "zh-Hant": "落霞與孤鶩齊飛,秋水共長天一色。",
    "ja": "色は匂へど 散りぬるを 我が世誰ぞ 常ならむ",
    "ko": "다람쥐 헌 쳇바퀴에 타고파",
    "latin": "Sphinx of black quartz, judge my vow. 0123456789",
}


def core_text() -> str:
    """核心包字符:可打印 ASCII + 平/片假名 + 谚文兼容字母 + 全部默认样例句。"""
    parts = [
        "".join(chr(c) for c in range(0x20, 0x7F)),
        "".join(chr(c) for c in range(0x3041, 0x3097)),
        "".join(chr(c) for c in range(0x30A1, 0x30FB)),
        "".join(chr(c) for c in range(0x3131, 0x318F)),
        *SAMPLES.values(),
    ]
    return "".join(parts)


CORE_TEXT = core_text()
