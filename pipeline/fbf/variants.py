"""简繁异体字归一化:让搜索「东云」能命中「東雲」,反之亦然。

数据来自 Unicode Unihan 的 kSimplifiedVariant / kTraditionalVariant,
合并成等价类(见 textdata/st-variants.txt)。展开在构建期完成——
索引里直接存好各种写法,前端不必加载映射表。
"""

from __future__ import annotations

import functools
from pathlib import Path

DATA = Path(__file__).parent / "textdata" / "st-variants.txt"


@functools.cache
def variant_map(path: Path = DATA) -> dict[str, str]:
    """字 → 该字所属等价类的全部写法(含自身)。"""
    table: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for ch in line:
            table[ch] = line
    return table


def expand(text: str) -> str:
    """把文本展开成「原文 + 各字的其它写法」,供搜索匹配。

    仅对有异体的汉字展开;无异体的字符原样保留。
    """
    if not text:
        return ""
    table = variant_map()
    extra: list[str] = []
    for ch in text:
        group = table.get(ch)
        if group:
            others = group.replace(ch, "")
            if others:
                extra.append(others)
    return text + ("".join(extra) if extra else "")


def search_text(*fields: str) -> str:
    """把若干字段拼成一条可搜索文本,并做简繁展开。"""
    joined = " ".join(f for f in fields if f)
    return expand(joined)
