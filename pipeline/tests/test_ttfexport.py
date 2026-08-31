from pathlib import Path

import pytest

from opf.ingest.otb import convert_otb
from opf.metrics import glyph_ink_size
from opf.parsers.bdf import parse_bdf
from opf.ttfexport import build_ttf, glyph_name

FIX = Path(__file__).parent / "fixtures"


def _mini():
    return parse_bdf(FIX / "mini.bdf", "mini")


def test_glyph_names():
    assert glyph_name(0x41) == "uni0041"
    assert glyph_name(0x6C38) == "uni6C38"
    assert glyph_name(0x20000) == "u20000"


def test_single_size_roundtrip(tmp_path):
    src = _mini()
    out = tmp_path / "mini.ttf"
    info = build_ttf([src], "Mini", "Regular", out)
    assert info["strikes"] == 1 and info["glyphs"] == 2
    assert out.exists() and out.stat().st_size > 0

    back = convert_otb(out, "mini")
    assert len(back) == 1
    suffix, rt = back[0]
    assert suffix == "16px"
    src_by = {g.cp: g for g in src.glyphs}
    rt_by = {g.cp: g for g in rt.glyphs}
    assert set(rt_by) == set(src_by)
    for cp, g in src_by.items():
        r = rt_by[cp]
        assert (r.bbw, r.bbh) == (g.bbw, g.bbh), f"U+{cp:04X} 尺寸"
        assert r.dwidth == g.dwidth, f"U+{cp:04X} 步进"
        assert r.rows == g.rows, f"U+{cp:04X} 位图"
        assert glyph_ink_size(r) == glyph_ink_size(g)


def test_multi_size_strikes(tmp_path):
    """同一字体的多个尺寸应打进同一个 TTF 的多个 strike。"""
    real = FIX / "real-galmuri7.bdf"
    if not real.exists():
        pytest.skip("no real fixture")
    small = parse_bdf(real, "g")
    big = _mini()  # 16px，与 galmuri7 尺寸不同即可
    out = tmp_path / "multi.ttf"
    info = build_ttf([small, big], "Multi", "Regular", out)
    assert info["strikes"] == 2
    assert sorted(info["sizes"]) == sorted([small.pixel_size, big.pixel_size])

    strikes = convert_otb(out, "multi")
    assert {s for s, _ in strikes} == {f"{small.pixel_size}px", f"{big.pixel_size}px"}
    # 每个 strike 只含该尺寸实际有的字形
    by_suffix = {s: f for s, f in strikes}
    small_cps = {g.cp for g in by_suffix[f"{small.pixel_size}px"].glyphs}
    assert 0x41 in small_cps


def test_cmap_and_no_outlines(tmp_path):
    from fontTools.ttLib import TTFont

    out = tmp_path / "mini.ttf"
    build_ttf([_mini()], "Mini", "Regular", out)
    f = TTFont(out)
    assert "EBDT" in f and "EBLC" in f
    cmap = f.getBestCmap()
    assert 0x41 in cmap and 0x6C38 in cmap
    # 所有字形都是空轮廓：位图字体不带矢量数据
    glyf = f["glyf"]
    for name in f.getGlyphOrder():
        assert glyf[name].numberOfContours in (0, -1) or not glyf[name].isComposite()
        assert getattr(glyf[name], "numberOfContours", 0) == 0
    assert f["name"].getDebugName(1) == "Mini"
