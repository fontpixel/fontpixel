"""宣称大小与墨迹度量(spec §4.2 口径)。"""

from __future__ import annotations

from dataclasses import dataclass
from statistics import median_low

from pfc.model import Glyph, ParsedFont, row_bytes

# 每字节最高/最低置位位置(bit 0 = MSB = 最左像素)
_FIRST_SET = [8] * 256
_LAST_SET = [-1] * 256
for _b in range(1, 256):
    for _i in range(8):
        if _b & (0x80 >> _i):
            _FIRST_SET[_b] = min(_FIRST_SET[_b], _i)
            _LAST_SET[_b] = max(_LAST_SET[_b], _i)

_XH_LETTERS = frozenset(ord(c) for c in "acemnorsuvwxz")


@dataclass
class InkMetrics:
    han_ink: tuple[int, int] | None
    cap_height: int | None
    x_height: int | None
    max_ink: tuple[int, int]
    max_ink_cps: tuple[int, int]


def _is_cjk_ideograph(cp: int) -> bool:
    return (
        0x3400 <= cp <= 0x4DBF
        or 0x4E00 <= cp <= 0x9FFF
        or 0x20000 <= cp <= 0x3FFFF
    )


def glyph_ink_size(g: Glyph) -> tuple[int, int] | None:
    nb = row_bytes(g.bbw)
    if nb == 0 or g.bbh == 0:
        return None
    min_x, max_x = g.bbw, -1
    min_y, max_y = g.bbh, -1
    tail_bits = g.bbw - (nb - 1) * 8  # 末字节有效位数
    tail_mask = (0xFF00 >> tail_bits) & 0xFF if tail_bits < 8 else 0xFF
    for y in range(g.bbh):
        base = y * nb
        row_lit = False
        for bx in range(nb):
            b = g.rows[base + bx]
            if bx == nb - 1:
                b &= tail_mask
            if not b:
                continue
            row_lit = True
            x0 = bx * 8 + _FIRST_SET[b]
            x1 = bx * 8 + _LAST_SET[b]
            if x0 < min_x:
                min_x = x0
            if x1 > max_x:
                max_x = x1
        if row_lit:
            if y < min_y:
                min_y = y
            max_y = y
    if max_x < 0:
        return None
    return (max_x - min_x + 1, max_y - min_y + 1)


def compute_ink(f: ParsedFont, han_ref: frozenset[int]) -> InkMetrics:
    ink_cache: dict[int, tuple[int, int] | None] = {}

    def ink(g: Glyph) -> tuple[int, int] | None:
        if g.cp not in ink_cache:
            ink_cache[g.cp] = glyph_ink_size(g)
        return ink_cache[g.cp]

    han_glyphs = [g for g in f.glyphs if g.cp in han_ref]
    if len(han_glyphs) < 100:
        han_glyphs = [g for g in f.glyphs if _is_cjk_ideograph(g.cp)]
    han_sizes = [s for g in han_glyphs if (s := ink(g)) is not None]
    han_ink = None
    if han_sizes:
        han_ink = (
            median_low([s[0] for s in han_sizes]),
            median_low([s[1] for s in han_sizes]),
        )

    cap_hs = [
        s[1]
        for g in f.glyphs
        if ord("A") <= g.cp <= ord("Z") and (s := ink(g)) is not None
    ]
    x_hs = [s[1] for g in f.glyphs if g.cp in _XH_LETTERS and (s := ink(g)) is not None]

    max_w, max_h = 0, 0
    max_w_cp, max_h_cp = 0, 0
    for g in f.glyphs:
        s = ink(g)
        if s is None:
            continue
        if s[0] > max_w:
            max_w, max_w_cp = s[0], g.cp
        if s[1] > max_h:
            max_h, max_h_cp = s[1], g.cp

    return InkMetrics(
        han_ink=han_ink,
        cap_height=median_low(cap_hs) if cap_hs else None,
        x_height=median_low(x_hs) if x_hs else None,
        max_ink=(max_w, max_h),
        max_ink_cps=(max_w_cp, max_h_cp),
    )


def is_monospaced(f: ParsedFont) -> bool:
    widths = [g.dwidth for g in f.glyphs if g.dwidth > 0]
    if not widths:
        return False
    counts: dict[int, int] = {}
    for w in widths:
        counts[w] = counts.get(w, 0) + 1
    modal = max(counts.values())
    return modal / len(widths) >= 0.99


def claimed_size(f: ParsedFont) -> int:
    return f.pixel_size
