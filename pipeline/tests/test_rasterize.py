import zipfile
from pathlib import Path

import pytest

from fbf.ingest.rasterize import detect_native_ppem, rasterize_ttf
from fbf.model import row_bytes
from fbf.parsers.bdf import parse_bdf

COLLECTION = Path("/home/chen/githubprojects/pixelfontworkshop/pixel-font-collection-fonts")
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
    # 注意:格点 ppem(em 相对)与 BDF 的 PIXEL_SIZE 是两种口径,
    # 不必相等;正确性由位图逐像素对照测试保证。
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
    # 矢量化往返允许极少量取整差异,但必须 ≥99% 逐像素一致
    assert mismatch <= len(checked) * 0.01, f"{mismatch}/{len(checked)} 不一致"


def test_regular_outline_font_returns_none():
    dejavu = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    if not dejavu.exists():
        pytest.skip("no system DejaVu")
    assert detect_native_ppem(dejavu) is None
