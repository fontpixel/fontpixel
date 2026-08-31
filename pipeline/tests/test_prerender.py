import re
from pathlib import Path

from opf.parsers.bdf import parse_bdf
from opf.prerender import og_png, sample_svg

FIX = Path(__file__).parent / "fixtures"


def _mini():
    return parse_bdf(FIX / "mini.bdf", "mini")


def test_svg_rect_runs_and_viewbox():
    svg = sample_svg(_mini(), "A")
    # A 的水平游程数:1+1+2+2+2+1+2+2+2+2 = 17
    assert svg.count("<rect") == 17
    assert 'viewBox="0 0 8 16"' in svg
    assert 'shape-rendering="crispEdges"' in svg


def test_svg_missing_placeholder():
    svg = sample_svg(_mini(), "B")
    assert 'class="missing"' in svg


def test_svg_multichar_advances():
    svg = sample_svg(_mini(), "AA")
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    assert m and m.group(1) == "16"  # 两个 A,各 dwidth 8


def test_og_png(tmp_path):
    out = tmp_path / "og.png"
    og_png(_mini(), "Mini Font", "A永A", out)
    from PIL import Image

    img = Image.open(out)
    assert img.size == (1200, 630)
    assert img.mode in ("RGB", "RGBA")


def test_svg_deterministic():
    assert sample_svg(_mini(), "A永") == sample_svg(_mini(), "A永")


def test_missing_space_renders_blank_not_a_box():
    """CJK 点阵字体常只有全角空格 U+3000，没有半角 U+0020。

    空白没有墨迹，缺了也不该画成缺字虚线框——任何排版引擎都按空白推进。
    """
    f = _mini()
    assert not any(g.cp == 0x20 for g in f.glyphs), "夹具本身就没有半角空格"
    assert 'class="missing"' not in sample_svg(f, "永 永"), "空格不该被画成缺字框"
    # 换成真正缺失的字，框还是要画
    assert 'class="missing"' in sample_svg(f, "永B永")
