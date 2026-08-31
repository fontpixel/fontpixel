from pathlib import Path

import pytest

from opf.parsers.bdf import parse_bdf
from opf.vectorize import _rects, build_vector_ttf

FIX = Path(__file__).parent / "fixtures"


def _mini():
    return parse_bdf(FIX / "mini.bdf", "mini")


class _G:
    """A minimal glyph built from an ASCII-art drawing."""

    def __init__(self, art: list[str]):
        self.bbw = len(art[0])
        self.bbh = len(art)
        self.bbx = 0
        self.bby = 0
        nb = (self.bbw + 7) // 8
        rows = bytearray()
        for line in art:
            v = 0
            for i, ch in enumerate(line):
                if ch == "#":
                    v |= 0x80 >> (i % 8)
                if i % 8 == 7 or i == len(line) - 1:
                    rows.append(v)
                    v = 0
            while len(rows) % nb:
                rows.append(0)
        self.rows = bytes(rows)


def test_rects_merges_horizontally_and_vertically():
    from opf.vectorize import _lit_rows

    # a 2x2 solid block should merge into one rectangle
    block = _G(["##", "##"])
    assert _rects(_lit_rows(block)) == [(0, 0, 2, 2)]

    # a single pixel
    dot = _G([".#.", "...", "..."])
    assert _rects(_lit_rows(dot)) == [(1, 0, 1, 1)]

    # two rows of different widths stacked don't merge
    step = _G(["##.", "###"])
    got = sorted(_rects(_lit_rows(step)))
    assert got == [(0, 0, 2, 1), (0, 1, 3, 1)]

    # empty glyph
    assert _rects(_lit_rows(_G(["..", ".."]))) == []


def test_square_ttf_has_real_outlines(tmp_path):
    from fontTools.ttLib import TTFont

    out = tmp_path / "sq.ttf"
    info = build_vector_ttf(_mini(), "Mini", "Regular", out, shape="square")
    assert info["shape"] == "square" and info["glyphs"] == 2
    f = TTFont(out)
    assert "EBDT" not in f and "EBLC" not in f  # this is a vector font
    glyf = f["glyf"]
    a = glyf[f.getBestCmap()[0x41]]
    assert a.numberOfContours > 0, "A 必须有真实轮廓"
    unit = f["head"].unitsPerEm // 16
    # the outline only covers the lit pixels, not the whole BBX: A's ink is 6 columns x 10 rows
    from opf.metrics import glyph_ink_size

    src_a = next(g for g in _mini().glyphs if g.cp == 0x41)
    iw, ih = glyph_ink_size(src_a)
    assert a.xMax - a.xMin == iw * unit
    assert a.yMax - a.yMin == ih * unit


def test_round_reuses_one_dot_via_components(tmp_path):
    """The round-dot variant must reuse a single circle: store one outline plus a
    per-pixel offset, rather than a full outline for every pixel -- the latter
    would make the file more than three times larger."""
    from fontTools.ttLib import TTFont

    out = tmp_path / "rd.ttf"
    build_vector_ttf(_mini(), "Mini", "Regular", out, shape="round")
    f = TTFont(out)
    # post 3.0 stores no glyph names, so the base circle is located by glyph index (right after .notdef)
    dot_name = f.getGlyphOrder()[1]
    dot = f["glyf"][dot_name]
    _, _, flags = dot.getCoordinates(f["glyf"])
    assert any(fl & 0x01 == 0 for fl in flags), "基准圆应含离线控制点(曲线)"
    assert dot.numberOfContours == 1

    a = f["glyf"][f.getBestCmap()[0x41]]
    assert a.isComposite(), "字形应是引用基准圆的复合字形"
    lit = sum(bin(b).count("1") for b in _mini().glyphs[0].rows)
    assert len(a.components) == lit
    assert {c.glyphName for c in a.components} == {dot_name}


def test_square_merges_runs(tmp_path):
    """The square variant merges adjacent pixels into rectangles, so the contour count should be less than the lit-pixel count."""
    from fontTools.ttLib import TTFont

    sq = tmp_path / "s.ttf"
    build_vector_ttf(_mini(), "M", "R", sq, shape="square")
    fs = TTFont(sq)
    src = next(g for g in _mini().glyphs if g.cp == 0x6C38)
    lit = sum(bin(b).count("1") for b in src.rows)
    assert 0 < fs["glyf"][fs.getBestCmap()[0x6C38]].numberOfContours < lit


def test_metrics_scale_with_pixel_size(tmp_path):
    from fontTools.ttLib import TTFont

    src = _mini()
    out = tmp_path / "m.ttf"
    build_vector_ttf(src, "Mini", "Regular", out, shape="square")
    f = TTFont(out)
    upem = f["head"].unitsPerEm
    unit = upem // src.pixel_size
    hmtx = f["hmtx"]
    a_src = next(g for g in src.glyphs if g.cp == 0x41)
    assert hmtx[f.getBestCmap()[0x41]][0] == a_src.dwidth * unit


def test_rejects_bad_shape(tmp_path):
    with pytest.raises(ValueError):
        build_vector_ttf(_mini(), "M", "R", tmp_path / "x.ttf", shape="triangle")


def test_timestamps_pinned(tmp_path):
    """The head timestamp must be pinned, or identical input would produce different
    bytes on every build, and CI would re-upload every TTF each time."""
    from fontTools.ttLib import TTFont

    from opf.ttfexport import FIXED_TIMESTAMP, build_ttf

    out = tmp_path / "v.ttf"
    build_vector_ttf(_mini(), "M", "R", out, shape="square")
    head = TTFont(out)["head"]
    assert head.created == FIXED_TIMESTAMP and head.modified == FIXED_TIMESTAMP

    bmp = tmp_path / "b.ttf"
    build_ttf([_mini()], "M", "R", bmp)
    head = TTFont(bmp)["head"]
    assert head.created == FIXED_TIMESTAMP and head.modified == FIXED_TIMESTAMP


def _padded_font():
    """Contains a glyph whose ink doesn't start at column 0 -- the full-width left parenthesis is this shape."""
    from opf.model import Glyph, ParsedFont

    def g(cp, art, bbx=0, dwidth=12):
        base = _G(art)
        return Glyph(cp=cp, name=f"g{cp}", dwidth=dwidth, bbw=base.bbw,
                     bbh=base.bbh, bbx=bbx, bby=0, rows=base.rows)

    glyphs = [
        g(0x41, ["##......", "#.#.....", "##......"]),          # ink flush left
        g(0xFF08, ["......##", ".....#..", "......##"]),        # ink entirely on the right
        g(0x42, ["..##....", ".#..#...", "..##...."], bbx=-2),  # negative bbx
    ]
    return ParsedFont(path=Path("t.bdf"), family_slug="t", file_name="t.bdf",
                      props={}, pixel_size=12, ascent=10, descent=2,
                      bbox=(12, 12, -2, -2), glyphs=glyphs, warnings=[])


@pytest.mark.parametrize("shape", ["square", "round"])
def test_lsb_matches_outline_xmin(tmp_path, shape):
    """hmtx's lsb must equal the outline's xMin.

    TrueType renderers shift a glyph by the difference between lsb and xMin: if lsb
    were written as bbx, a glyph like "(" whose ink sits entirely on the right side
    of its cell would get shifted left as a whole and collide with the previous
    character -- exactly how this surfaced on the station-name web font.
    """
    from fontTools.ttLib import TTFont

    font = _padded_font()
    out = tmp_path / "v.ttf"
    build_vector_ttf(font, "T", "Regular", out, shape=shape)
    f = TTFont(out)
    glyf, hmtx = f["glyf"], f["hmtx"]
    checked = 0
    for name in f.getGlyphOrder():
        g = glyf[name]
        if g.numberOfContours == 0 and not g.isComposite():
            continue
        assert hmtx[name][1] == g.xMin, name
        checked += 1
    assert checked > 0
