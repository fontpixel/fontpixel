"""Coverage engine: charset stats, overview, badges, and script detection."""

from __future__ import annotations

from opf.coverage.charsets import Charset
from opf.coverage.ucd import Ucd
from opf.model import ParsedFont

# 12 code points in the compatibility block that are actually unified ideographs (per Unicode's official notes)
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

# Badges: (badge id = charset id, threshold)
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


# Script detection: two tiers per script
#   full     coverage clears the threshold — the language can be written normally
#   partial  clearly targets the language but falls short of the threshold (e.g. a
#            "Japanese" font with kana but no kanji, or a Korean font that only
#            covers the KS X 1001 hanja subset)
# Detection uses the same coverage data as the Coverage filter, but with a different
# question in mind: this answers "can you write in this language", while Coverage
# answers "does it meet some standard's compliance bar".
SCRIPT_FULL = 0.9      # threshold to count as "full"
SCRIPT_TARGET = 0.1    # lower bound for "clearly targets this language"
KANA_GATE = 0.95       # no kana means it can't be "targeting Japanese"

# Reference charsets used to detect each script. The site's coverage filter
# dropdown must list all of these, or users will see e.g. "Simplified Chinese
# (incomplete)" with no matching filter to select by the same yardstick.
SCRIPT_REFERENCE_CHARSETS: dict[str, tuple[str, ...]] = {
    "zh-hans": ("gb2312", "tongyong-guifan"),
    "zh-hant": ("big5-changyong",),
    "ja": ("jisx0208-l1", "hiragana", "katakana"),
    "ko": ("ksx1001-hangul", "hangul-syllables"),
    "latin": ("latin-basic",),
    "latin-supp": ("latin1-supp",),
    "latin-ext": ("latin-ext-a",),
    "cyrillic": ("cyrillic",),
    "greek": ("greek-coptic",),
}


def _best(cov: dict[str, tuple[int, int]], ids: tuple[str, ...]) -> float:
    return max(_ratio(cov, i) for i in ids)


def _script_scores(cov: dict[str, tuple[int, int]]) -> dict[str, float]:
    r = SCRIPT_REFERENCE_CHARSETS
    kana = min(_ratio(cov, "hiragana"), _ratio(cov, "katakana"))
    return {
        "zh-hans": _best(cov, r["zh-hans"]),
        "zh-hant": _best(cov, r["zh-hant"]),
        # Japanese is judged by kanji coverage, but kana must be present first for it to count as targeting Japanese
        "ja": _ratio(cov, "jisx0208-l1") if kana >= KANA_GATE else 0.0,
        "ko": _best(cov, r["ko"]),
        "latin": _best(cov, r["latin"]),
        "latin-supp": _best(cov, r["latin-supp"]),
        "latin-ext": _best(cov, r["latin-ext"]),
        "cyrillic": _best(cov, r["cyrillic"]),
        "greek": _best(cov, r["greek"]),
    }


def detect_scripts(cov: dict[str, tuple[int, int]]) -> list[str]:
    """Scripts that clear the threshold; scripts that fall short but clearly target the language are recorded as `<script>-partial`."""
    out: list[str] = []
    for name, score in _script_scores(cov).items():
        if score >= SCRIPT_FULL:
            out.append(name)
        elif score >= SCRIPT_TARGET:
            out.append(f"{name}-partial")
    return out


def pick_sample_lang(cov: dict[str, tuple[int, int]]) -> str:
    """Sample language: script strength is scored on the same 0-1 scale for all scripts; fixed priority order, ties favor the earlier one."""
    scripts = {s for s in detect_scripts(cov) if not s.endswith("-partial")}
    ordered = [
        ("zh-hans", max(_ratio(cov, "gb2312"), _ratio(cov, "tongyong-guifan"))),
        ("zh-hant", _ratio(cov, "big5-changyong")),
        ("ko", max(_ratio(cov, "ksx1001-hangul"), _ratio(cov, "hangul-syllables"))),
        ("ja", 0.3 * (_ratio(cov, "hiragana") + _ratio(cov, "katakana")) / 2
               + 0.7 * _ratio(cov, "jisx0208-l1")),  # kanji coverage is the discriminating factor for "Japanese-ness"
        ("latin", 0.4 * _ratio(cov, "latin-basic")),
    ]
    best, best_v = "latin", -1.0
    for name, v in ordered:
        if name not in scripts and not (name == "latin" and not scripts):
            continue
        if v > best_v:
            best, best_v = name, v
    return {"zh-hans": "zh-Hans", "zh-hant": "zh-Hant", "ja": "ja", "ko": "ko",
            "latin": "latin"}[best]
