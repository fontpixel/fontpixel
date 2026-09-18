import os
import zipfile
from pathlib import Path

import pytest

from opf.ingest.rasterize import detect_native_ppem, rasterize_ttf
from opf.model import row_bytes
from opf.parsers.bdf import parse_bdf

# Sibling of the repo by default (the --src the README documents), so a moved
# checkout doesn't silently skip every test in this file. Override with
# OPF_COLLECTION.
COLLECTION = Path(
    os.environ.get("OPF_COLLECTION")
    or Path(__file__).resolve().parents[2].parent / "pixel-font-collection-fonts"
)
GALMURI_ZIP = COLLECTION / (
    "CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/quiple--galmuri/"
    "RELEASE-ASSETS/Galmuri-v2.40.4.zip"
)

pytestmark = pytest.mark.skipif(not COLLECTION.exists(), reason="collection missing")


@pytest.fixture(scope="module")
def galmuri9(tmp_path_factory):
    d = tmp_path_factory.mktemp("g9")
    with zipfile.ZipFile(GALMURI_ZIP) as z:
        for name in ("Galmuri9.ttf", "Galmuri9.bdf"):
            (d / name).write_bytes(z.read(name))
    return d


def _lit(g):
    nb = row_bytes(g.bbw)
    return {
        (g.bbx + x, g.bby + (g.bbh - 1 - y))
        for y in range(g.bbh)
        for x in range(g.bbw)
        if g.rows[y * nb + (x >> 3)] & (0x80 >> (x & 7))
    }


def test_detect_native_ppem_on_vectorized_pixel_font(galmuri9):
    # note: the grid ppem (em-relative) and the BDF's PIXEL_SIZE are two different
    # measures and need not be equal; correctness is guaranteed by the pixel-by-pixel
    # bitmap comparison test.
    ppem = detect_native_ppem(galmuri9 / "Galmuri9.ttf")
    assert ppem is not None
    assert 4 <= ppem <= 64


def test_rasterized_matches_official_bdf(galmuri9):
    ppem = detect_native_ppem(galmuri9 / "Galmuri9.ttf")
    assert ppem is not None
    rf = rasterize_ttf(galmuri9 / "Galmuri9.ttf", ppem, "galmuri9")
    bf = parse_bdf(galmuri9 / "Galmuri9.bdf", "g9")
    r_by = {g.cp: g for g in rf.glyphs}
    b_by = {g.cp: g for g in bf.glyphs}
    common = sorted(set(r_by) & set(b_by))
    assert len(common) > 10000
    mismatch = 0
    checked = common[:200] + common[len(common) // 2 : len(common) // 2 + 200]
    for cp in checked:
        if _lit(r_by[cp]) != _lit(b_by[cp]) or r_by[cp].dwidth != b_by[cp].dwidth:
            mismatch += 1
    # the vectorize round-trip allows a tiny amount of rounding difference, but must be >=99% pixel-identical
    assert mismatch <= len(checked) * 0.01, f"{mismatch}/{len(checked)} 不一致"


def test_regular_outline_font_returns_none():
    dejavu = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not dejavu.exists():
        pytest.skip("no system DejaVu")
    assert detect_native_ppem(dejavu) is None


# Nightgazer12 is a vectorized pixel font whose outlines sit exactly on a 12px grid
# (upem=24, every coordinate a multiple of 2), so the correct raster is fully determined
# by the geometry — filling the contours at pixel centres. These two glyphs were derived
# that way, independently of FreeType.
NIGHTGAZER12 = COLLECTION / (
    "pixel-fonts-supplement-zeoseven-maoken-2026-08-18/Upstream-GitHub/"
    "scott0107000--Nightgazer-Bitmap/Nightgazer-Bitmap-HEAD/Nightgazer12.ttf"
)
_GRID_TRUTH = {
    0x570B: (10, 11, 1, -1, 12, [  # 國
        "##########",
        "#....#.#.#",
        "##########",
        "#....#...#",
        "####.#.#.#",
        "##.#.#.#.#",
        "####.##..#",
        "#....#.#.#",
        "#####.##.#",
        "#......#.#",
        "##########",
    ]),
    0x5B57: (11, 11, 0, -1, 12, [  # 字
        ".....#.....",
        ".##########",
        ".#........#",
        "#.########.",
        ".......#...",
        "......#....",
        "###########",
        "......#....",
        "...#..#....",
        "....###....",
        ".....#.....",
    ]),
}


def _art(g):
    nb = row_bytes(g.bbw)
    return [
        "".join("#" if g.rows[y * nb + (x >> 3)] & (0x80 >> (x & 7)) else "."
                for x in range(g.bbw))
        for y in range(g.bbh)
    ]


@pytest.mark.skipif(not NIGHTGAZER12.exists(), reason="Nightgazer12.ttf missing")
def test_rasterize_reproduces_the_grid_exactly():
    """A font already on the pixel grid must come back pixel-identical.

    FreeType hints by default, and on a pixel font the hinter shifts and doubles
    1px stems — 一会儿粗一会儿细. Rasterizing has to switch it off.
    """
    rf = rasterize_ttf(NIGHTGAZER12, 12, "nightgazer")
    by_cp = {g.cp: g for g in rf.glyphs}
    for cp, (bbw, bbh, bbx, bby, dwidth, art) in _GRID_TRUTH.items():
        g = by_cp[cp]
        assert _art(g) == art, f"U+{cp:04X} raster differs from the outline grid"
        assert (g.bbw, g.bbh, g.bbx, g.bby, g.dwidth) == (bbw, bbh, bbx, bby, dwidth)

    # ...and hinting=True is what the caller opts into, not the default.
    hinted = {g.cp: g for g in rasterize_ttf(NIGHTGAZER12, 12, "n", hinting=True).glyphs}
    assert _art(hinted[0x5B57]) != _GRID_TRUTH[0x5B57][5]
