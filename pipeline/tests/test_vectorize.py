from pathlib import Path

import pytest

from opf.parsers.bdf import parse_bdf
from opf.vectorize import _rects, build_vector_ttf

FIX = Path(__file__).parent / "fixtures"


def _mini():
    return parse_bdf(FIX / "mini.bdf", "mini")


class _G:
    """按 ASCII 画构造的最小字形。"""

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

    # 2×2 实心块应合成一个矩形
    block = _G(["##", "##"])
    assert _rects(_lit_rows(block)) == [(0, 0, 2, 2)]

    # 单像素
    dot = _G([".#.", "...", "..."])
    assert _rects(_lit_rows(dot)) == [(1, 0, 1, 1)]

    # 上下不同宽的两行不合并
    step = _G(["##.", "###"])
    got = sorted(_rects(_lit_rows(step)))
    assert got == [(0, 0, 2, 1), (0, 1, 3, 1)]

    # 空字形
    assert _rects(_lit_rows(_G(["..", ".."]))) == []


def test_square_ttf_has_real_outlines(tmp_path):
    from fontTools.ttLib import TTFont

    out = tmp_path / "sq.ttf"
    info = build_vector_ttf(_mini(), "Mini", "Regular", out, shape="square")
    assert info["shape"] == "square" and info["glyphs"] == 2
    f = TTFont(out)
    assert "EBDT" not in f and "EBLC" not in f  # 这是矢量字体
    glyf = f["glyf"]
    a = glyf[f.getBestCmap()[0x41]]
    assert a.numberOfContours > 0, "A 必须有真实轮廓"
    unit = f["head"].unitsPerEm // 16
    # 轮廓只覆盖点亮的像素，不是整个 BBX：A 的墨迹是 6 列 × 10 行
    from opf.metrics import glyph_ink_size

    src_a = next(g for g in _mini().glyphs if g.cp == 0x41)
    iw, ih = glyph_ink_size(src_a)
    assert a.xMax - a.xMin == iw * unit
    assert a.yMax - a.yMin == ih * unit


def test_round_reuses_one_dot_via_components(tmp_path):
    """圆点版必须复用同一个圆:存一份轮廓 + 每像素一个偏移,而不是逐像素
    各存一整圈轮廓——后者文件大三倍多。"""
    from fontTools.ttLib import TTFont

    out = tmp_path / "rd.ttf"
    build_vector_ttf(_mini(), "Mini", "Regular", out, shape="round")
    f = TTFont(out)
    # post 3.0 不存字形名，基准圆按字形序号定位（紧跟 .notdef）
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
    """方块版会把相邻像素合并成矩形,轮廓数应少于亮像素数。"""
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
    """head 时间戳必须固定,否则同样的输入每次构建都产出不同字节,
    CI 会把全部 TTF 重新上传一遍。"""
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
    """含「墨迹不从第 0 列开始」的字形——全角左括号就是这种形态。"""
    from opf.model import Glyph, ParsedFont

    def g(cp, art, bbx=0, dwidth=12):
        base = _G(art)
        return Glyph(cp=cp, name=f"g{cp}", dwidth=dwidth, bbw=base.bbw,
                     bbh=base.bbh, bbx=bbx, bby=0, rows=base.rows)

    glyphs = [
        g(0x41, ["##......", "#.#.....", "##......"]),          # 墨迹贴左
        g(0xFF08, ["......##", ".....#..", "......##"]),        # 墨迹全在右侧
        g(0x42, ["..##....", ".#..#...", "..##...."], bbx=-2),  # 负 bbx
    ]
    return ParsedFont(path=Path("t.bdf"), family_slug="t", file_name="t.bdf",
                      props={}, pixel_size=12, ascent=10, descent=2,
                      bbox=(12, 12, -2, -2), glyphs=glyphs, warnings=[])


@pytest.mark.parametrize("shape", ["square", "round"])
def test_lsb_matches_outline_xmin(tmp_path, shape):
    """hmtx 的 lsb 必须等于轮廓 xMin。

    TrueType 渲染器按 lsb 与 xMin 之差平移字形：lsb 写成 bbx 的话，
    「（」这类墨迹全在格子右侧的字形会被整体左移、撞进前一个字——
    站名 web 字体上就是这么露馅的。
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
