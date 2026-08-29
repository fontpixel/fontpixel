from pathlib import Path

import pytest

from fbf.ingest.extract import extract_zip
from fbf.ingest.kbitx import convert_kbitx
from fbf.ingest.otb import convert_otb
from fbf.ingest.run import run_manifest
from fbf.metrics import glyph_ink_size
from fbf.parsers.bdf import parse_bdf

COLLECTION = Path("/home/chen/githubprojects/pixelfontworkshop/pixel-font-collection-fonts")
GALMURI = COLLECTION / "CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/quiple--galmuri"
WQY = COLLECTION / (
    "CJK-bitmap-fonts-open-source-2026-08-18/Chinese/carrothu-cn--wqy-bitmapfont-otb"
)

pytestmark = pytest.mark.skipif(
    not COLLECTION.exists(), reason="collection folder missing"
)


def test_extract_zip_take(tmp_path):
    out = extract_zip(
        GALMURI / "RELEASE-ASSETS/Galmuri-v2.40.4.zip",
        ["Galmuri9.bdf", "Galmuri7.bdf"],
        tmp_path,
    )
    names = sorted(p.name for p in out)
    assert names == ["Galmuri7.bdf", "Galmuri9.bdf"]
    f = parse_bdf(tmp_path / "Galmuri9.bdf", "g")
    assert len(f.glyphs) > 10000


def test_otb_conversion(tmp_path):
    fonts = convert_otb(WQY / "wenquanyi_9pt.otb", "wqy-bitmap")
    assert len(fonts) == 1
    suffix, f = fonts[0]
    assert suffix == "12px"
    assert f.pixel_size == 12
    yong = next(g for g in f.glyphs if g.cp == 0x6C38)
    assert (yong.bbw, yong.bbh, yong.dwidth) == (11, 11, 12)
    assert glyph_ink_size(yong) is not None
    assert len(f.glyphs) > 20000
    cps = [g.cp for g in f.glyphs]
    assert cps == sorted(cps)


def test_kbitx_matches_official_bdf():
    """galmuri 同时发布 kbitx 源与 BDF:逐像素对照验证解码器。"""
    kf = convert_kbitx(GALMURI / "src/Galmuri9.kbitx", "galmuri9")
    bf = parse_bdf(GALMURI / "dist/Galmuri9.bdf", "galmuri9")
    k_by = {g.cp: g for g in kf.glyphs}
    b_by = {g.cp: g for g in bf.glyphs}
    common = sorted(set(k_by) & set(b_by))
    assert len(common) > 10000

    def lit(g):
        from fbf.model import row_bytes

        nb = row_bytes(g.bbw)
        return {
            (g.bbx + x, g.bby + (g.bbh - 1 - y))
            for y in range(g.bbh)
            for x in range(g.bbw)
            if g.rows[y * nb + (x >> 3)] & (0x80 >> (x & 7))
        }

    for cp in common[:300] + common[-300:] + common[5000:5300]:
        kg, bg = k_by[cp], b_by[cp]
        assert kg.dwidth == bg.dwidth, f"U+{cp:04X} advance"
        assert lit(kg) == lit(bg), f"U+{cp:04X} bitmap"


def test_run_manifest_idempotent(tmp_path):
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        f"""
[[family]]
slug = "galmuri"
source = "CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/quiple--galmuri"
zip = "RELEASE-ASSETS/Galmuri-v2.40.4.zip"
zip_take = ["Galmuri7.bdf"]
license_files = ["ofl.md"]
name = "Galmuri"
repository = "https://github.com/quiple/galmuri"
provenance_url = "https://github.com/quiple/galmuri/releases"
form = "gothic"
""",
        encoding="utf-8",
    )
    dest = tmp_path / "fonts"
    report1 = run_manifest(manifest, COLLECTION, dest)
    assert report1.imported == ["galmuri"]
    assert (dest / "galmuri" / "Galmuri7.bdf").exists()
    assert (dest / "galmuri" / "ofl.md").exists()
    toml = (dest / "galmuri" / "family.toml").read_text(encoding="utf-8")
    assert 'name = "Galmuri"' in toml
    assert "provenance" in toml
    assert 'form = "gothic"' in toml
    assert "# UNVERIFIED" in toml  # 预填风格待人工复核

    report2 = run_manifest(manifest, COLLECTION, dest)
    assert report2.imported == []
    assert report2.skipped == ["galmuri"]
    # 用户改过的 family.toml 不被覆盖
    p = dest / "galmuri" / "family.toml"
    p.write_text(toml.replace('form = "gothic"', 'form = "rounded"'), encoding="utf-8")
    run_manifest(manifest, COLLECTION, dest)
    assert 'form = "rounded"' in p.read_text(encoding="utf-8")


def test_uwttyp0_unicode_remap(tmp_path):
    """UW ttyp0 用字体自有编码分发，须按 mgl/unicode.mgl 的字形名映射重建。"""
    from fbf.ingest.uwttyp0 import convert, load_unicode_map

    repo = COLLECTION / "github-clones-2026-08-29/uw-ttyp0-1.3"
    if not repo.exists():
        pytest.skip("uw-ttyp0 upstream not downloaded")
    mgl = repo / "mgl" / "unicode.mgl"
    table = load_unicode_map(mgl)
    assert table["LtCapA"] == 0x41
    assert table["LtCapALdot"] == 0x1EA0  # Ạ

    f = convert(repo / "bdf" / "t0-16.bdf", mgl, "uw-ttyp0")
    cps = {g.cp for g in f.glyphs}
    assert len(cps) > 2000
    for cp in (0x41, 0xE9, 0x1EA0, 0x3B1, 0x2500):
        assert cp in cps, hex(cp)
    assert f.props["CHARSET_REGISTRY"] == "ISO10646"
    # 原始自有编码不得残留
    assert 735 not in cps or 0x2DF == 735
