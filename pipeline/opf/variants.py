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


# 一个字段最多展开成这么多种写法。真实的字体名变体字很少，够用；
# 万一遇到变体字特别多的串，就只展开靠前的几个位置，不让组合数失控。
_MAX_RENDERINGS = 64


def expand(text: str) -> str:
    """把文本展开成「原文 + 各种简繁异体写法」,供搜索匹配。

    不能按下标取等价类的第 i 个成员——textdata/st-variants.txt 里各组的
    成员顺序并不统一(「驛驿」繁体在前,「点點」简体在前),那样只会拼出
    「文泉驛点阵宋体」这种混合体,全繁和全简的写法反而都搜不到。
    所以逐字做笛卡尔积,把该串所有写法都列出来。
    """
    if not text:
        return ""
    table = variant_map()
    outs = [""]
    for ch in text:
        group = table.get(ch)
        # 组合数超上限后，余下的字保持原样，至少不丢原文这一支
        if not group or len(outs) * len(group) > _MAX_RENDERINGS:
            outs = [o + ch for o in outs]
        else:
            outs = [o + c for o in outs for c in group]
    seen = dict.fromkeys([text, *outs])
    return " ".join(seen)


def search_text(*fields: str) -> str:
    """把若干字段拼成一条可搜索文本,并做简繁展开。"""
    seen: list[str] = []
    for f in fields:
        if f and f not in seen:
            seen.append(f)
    # 逐字段展开：整串一起做笛卡尔积的话，变体字一多组合数就炸了
    return " ".join(expand(f) for f in seen)
