import re
from pathlib import Path

from fbf.parsers.bdf import parse_bdf
from fbf.prerender import og_png, sample_svg

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
