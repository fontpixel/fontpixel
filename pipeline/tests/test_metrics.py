from pathlib import Path

from fbf.metrics import claimed_size, compute_ink, glyph_ink_size, is_monospaced
from fbf.model import Glyph, ParsedFont


def _row(r: str) -> bytes:
    padded = r.ljust((len(r) + 7) // 8 * 8, "0")
    return bytes(int(padded[i : i + 8], 2) for i in range(0, len(padded), 8))


def _g(cp: int, w: int, h: int, bits: list[str], dwidth: int | None = None) -> Glyph:
    return Glyph(
        cp=cp, name=f"u{cp:x}", dwidth=w if dwidth is None else dwidth,
        bbw=w, bbh=h, bbx=0, bby=0, rows=b"".join(_row(r) for r in bits),
    )


def _sq(cp: int, side: int, box: int) -> Glyph:
    """box×box 实心方块居左上,放在 side×side 字形格里。"""
    bits = ["1" * box + "0" * (side - box)] * box + ["0" * side] * (side - box)
    return _g(cp, side, side, bits)


def _font(glyphs: list[Glyph], pixel_size: int = 16) -> ParsedFont:
    return ParsedFont(
        path=Path("x.bdf"), family_slug="x", file_name="x.bdf", props={},
        pixel_size=pixel_size, ascent=pixel_size - 2, descent=2,
        bbox=(pixel_size, pixel_size, 0, -2), glyphs=glyphs, warnings=[],
    )


def test_ink_bbox_trims_margins():
    g = _g(0x4E00, 8, 8, [
        "00000000", "00111100", "00100100", "00111100",
        "00000000", "00000000", "00000000", "00000000",
    ])
    assert glyph_ink_size(g) == (4, 3)


def test_ink_ignores_bits_beyond_width():
    # bbw=7,末位第 8 bit 不应计入
    g = Glyph(cp=65, name="A", dwidth=8, bbw=7, bbh=2, bbx=0, bby=0,
              rows=bytes([0b00000001, 0b00000001]))
    assert glyph_ink_size(g) is None


def test_empty_glyph_none():
    assert glyph_ink_size(_g(32, 8, 8, ["00000000"] * 8)) is None


def test_han_ink_median():
    f = _font([_sq(0x4E00, 16, 14), _sq(0x4E01, 16, 15), _sq(0x4E03, 16, 16)])
    ink = compute_ink(f, frozenset({0x4E00, 0x4E01, 0x4E03}))
    assert ink.han_ink == (15, 15)


def test_no_han_uses_latin_heights():
    glyphs = [_sq(cp, 16, 10) for cp in range(ord("A"), ord("Z") + 1)]
    glyphs += [_sq(cp, 16, 7) for cp in range(ord("a"), ord("z") + 1)]
    ink = compute_ink(_font(glyphs), frozenset())
    assert ink.han_ink is None
    assert ink.cap_height == 10
    assert ink.x_height == 7


def test_max_ink_and_argmax():
    f = _font([_sq(65, 16, 4), _sq(0x4E00, 16, 12), _sq(0xE000, 16, 16)])
    ink = compute_ink(f, frozenset())
    assert ink.max_ink == (16, 16)
    assert ink.max_ink_cps == (0xE000, 0xE000)


def test_monospace_tolerance():
    g99 = [_g(0x2000 + i, 8, 8, ["11111111"] * 8, dwidth=8) for i in range(99)]
    one = [_g(0x3000, 8, 8, ["11111111"] * 8, dwidth=4)]
    assert is_monospaced(_font(g99 + one)) is True
    g95 = g99[:95]
    five = [_g(0x3000 + i, 8, 8, ["11111111"] * 8, dwidth=4) for i in range(5)]
    assert is_monospaced(_font(g95 + five)) is False


def test_zero_dwidth_combining_ignored():
    g = [_g(0x2000 + i, 8, 8, ["11111111"] * 8, dwidth=8) for i in range(50)]
    marks = [_g(0x300 + i, 8, 8, ["11111111"] * 8, dwidth=0) for i in range(30)]
    assert is_monospaced(_font(g + marks)) is True


def test_claimed_size():
    assert claimed_size(_font([], pixel_size=12)) == 12
