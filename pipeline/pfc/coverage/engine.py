"""覆盖率引擎:字表统计、总览、徽章与书写系统判定。"""

from __future__ import annotations

from pfc.coverage.charsets import Charset
from pfc.coverage.ucd import Ucd
from pfc.model import ParsedFont

# 兼容区中实为统一表意字的 12 个码位(Unicode 官方注记)
UNIFIED_IN_COMPAT = frozenset({
    0xFA0E, 0xFA0F, 0xFA11, 0xFA13, 0xFA14, 0xFA1F,
    0xFA21, 0xFA23, 0xFA24, 0xFA27, 0xFA28, 0xFA29,
})

_UNIFIED_RANGES = [
    (0x4E00, 0x9FFF), (0x3400, 0x4DBF), (0x20000, 0x2A6DF), (0x2A700, 0x2B73F),
    (0x2B740, 0x2B81F), (0x2B820, 0x2CEAF), (0x2CEB0, 0x2EBEF), (0x2EBF0, 0x2EE5F),
    (0x30000, 0x3134F), (0x31350, 0x323AF), (0x323B0, 0x3347F),
]
_COMPAT_RANGES = [(0xF900, 0xFAFF), (0x2F800, 0x2FA1F)]

_PLANES = [("BMP", 0x0000, 0xFFFF), ("SMP", 0x10000, 0x1FFFF),
           ("SIP", 0x20000, 0x2FFFF), ("TIP", 0x30000, 0x3FFFF),
           ("SSP", 0xE0000, 0xEFFFF)]
_PUA = [("BMP PUA", 0xE000, 0xF8FF), ("Plane 15", 0xF0000, 0xFFFFD),
        ("Plane 16", 0x100000, 0x10FFFD)]

# 徽章:(badge id = charset id, 阈值)
_BADGES: list[tuple[str, float]] = [
    ("gb2312", 0.99), ("tongyong-guifan", 0.99), ("big5-changyong", 0.99),
    ("tw-changyong-4808", 0.99), ("jisx0208-l1", 0.99), ("ksx1001-hangul", 0.99),
    ("hangul-syllables", 0.999), ("wgl4", 0.99), ("cp437", 0.99),
]


def font_cps(f: ParsedFont) -> frozenset[int]:
    return frozenset(g.cp for g in f.glyphs)


def coverage_for(cps: frozenset[int], charsets: list[Charset]) -> dict[str, tuple[int, int]]:
    return {c.id: (len(cps & c.cps), len(c.cps)) for c in charsets}


def unicode_block_coverage(cps: frozenset[int], ucd: Ucd) -> list[tuple[str, int, int]]:
    out: list[tuple[str, int, int]] = []
    for name, start, end in ucd.blocks:
        total = ucd.block_assigned_counts.get(name, 0)
        if total == 0:
            continue
        have = sum(1 for cp in cps if start <= cp <= end)
        out.append((name, have, total))
    return out


def _count_in(cps: frozenset[int], ranges: list[tuple[int, int]],
              assigned: frozenset[int] | None = None) -> tuple[int, int]:
    have = sum(1 for cp in cps for a, b in ranges if a <= cp <= b)
    if assigned is None:
        total = sum(b - a + 1 for a, b in ranges)
    else:
        total = sum(1 for cp in assigned for a, b in ranges if a <= cp <= b)
    return have, total


def overview(cps: frozenset[int], ucd: Ucd) -> dict:
    covered_assigned = len(cps & ucd.assigned)
    planes = []
    for name, a, b in _PLANES:
        have = sum(1 for cp in cps if a <= cp <= b)
        total = sum(1 for cp in ucd.assigned if a <= cp <= b)
        planes.append((name, have, total))
    pua = []
    for name, a, b in _PUA:
        have = sum(1 for cp in cps if a <= cp <= b)
        pua.append((name, have, b - a + 1))
    han = _count_in(cps, _UNIFIED_RANGES, ucd.assigned)
    compat = _count_in(cps, _COMPAT_RANGES, ucd.assigned)
    note = (len(cps & UNIFIED_IN_COMPAT), len(UNIFIED_IN_COMPAT))
    return {
        "total": (covered_assigned, len(ucd.assigned)),
        "planes": planes,
        "pua": pua,
        "han_total": han,
        "compat": compat,
        "compat_unified_note": note,
    }


def _ratio(cov: dict[str, tuple[int, int]], cid: str) -> float:
    if cid not in cov:
        return 0.0
    have, total = cov[cid]
    return have / total if total else 0.0


def badges(cov: dict[str, tuple[int, int]]) -> list[str]:
    out = [cid for cid, thr in _BADGES if _ratio(cov, cid) >= thr]
    if _ratio(cov, "hiragana") >= 1.0 and _ratio(cov, "katakana") >= 1.0:
        out.append("kana")
    return out


def detect_scripts(cov: dict[str, tuple[int, int]]) -> list[str]:
    out: list[str] = []
    if _ratio(cov, "gb2312-l1") >= 0.5:
        out.append("zh-hans")
    if _ratio(cov, "big5-changyong") >= 0.5:
        out.append("zh-hant")
    if _ratio(cov, "hiragana") >= 0.9 and _ratio(cov, "katakana") >= 0.9:
        out.append("ja")
    if _ratio(cov, "ksx1001-hangul") >= 0.5 or _ratio(cov, "hangul-syllables") >= 0.2:
        out.append("ko")
    if _ratio(cov, "latin-basic") >= 0.9:
        out.append("latin")
    if _ratio(cov, "cyrillic") >= 0.5:
        out.append("cyrillic")
    if _ratio(cov, "greek-coptic") >= 0.5:
        out.append("greek")
    return out


def pick_sample_lang(cov: dict[str, tuple[int, int]]) -> str:
    scripts = detect_scripts(cov)
    strength = {
        "zh-hans": _ratio(cov, "gb2312-l1"),
        "zh-hant": _ratio(cov, "big5-changyong"),
        "ja": (_ratio(cov, "hiragana") + _ratio(cov, "katakana")) / 2
              * (1.0 + _ratio(cov, "jisx0208-l1")),
        "ko": max(_ratio(cov, "ksx1001-hangul"), _ratio(cov, "hangul-syllables")),
        "latin": _ratio(cov, "latin-basic") * 0.5,  # 拉丁几乎人人有,权重降低
    }
    best = "latin"
    best_v = -1.0
    for s in scripts:
        v = strength.get(s, 0.0)
        if v > best_v:
            best, best_v = s, v
    return {"zh-hans": "zh-Hans", "zh-hant": "zh-Hant", "ja": "ja", "ko": "ko",
            "latin": "latin", "cyrillic": "latin", "greek": "latin"}[best]
