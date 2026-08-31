from pathlib import Path

import pytest

from opf.ingest.extract import extract_archive, extract_zip
from opf.ingest.kbitx import convert_kbitx
from opf.ingest.otb import convert_otb
from opf.ingest.run import run_manifest
from opf.metrics import glyph_ink_size
from opf.parsers.bdf import parse_bdf

COLLECTION = Path("/home/chen/githubprojects/pixelfontworkshop/pixel-font-collection-fonts")
GALMURI = COLLECTION / "CJK-bitmap-fonts-open-source-2026-08-18/Pan-CJK/quiple--galmuri"
WQY = COLLECTION / (
    "CJK-bitmap-fonts-open-source-2026-08-18/Chinese/carrothu-cn--wqy-bitmapfont-otb"
)
TECATE = COLLECTION / "github-clones-2026-08-31/tecate-bitmap-fonts"

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
        from opf.model import row_bytes

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
    from opf.ingest.uwttyp0 import convert, load_unicode_map

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


def test_extract_archive_tar(tmp_path):
    """X11 时代的字体包是 .tar.gz，许可证只存在于包内。"""
    arc = TECATE / "archives/ohsnap-1.8.0.tar.gz"
    if not arc.exists():
        pytest.skip("tecate snapshot missing")
    out = extract_archive(arc, ["README.ohsnap"], tmp_path)
    assert [p.name for p in out] == ["README.ohsnap"]
    assert "GPLv2" in (tmp_path / "README.ohsnap").read_text(encoding="utf-8")


def test_license_from_tarball(tmp_path):
    """字体在 bitmap/<dir>/，许可证在平级的 archives/<x>.tar.gz 内。"""
    if not TECATE.exists():
        pytest.skip("tecate snapshot missing")
    manifest = tmp_path / "manifest.toml"
    manifest.write_text(
        """
[[family]]
slug = "stlarch"
source = "github-clones-2026-08-31/tecate-bitmap-fonts/bitmap/stlarch"
take = ["stlarch.pcf"]
license_from = "github-clones-2026-08-31/tecate-bitmap-fonts/archives/stlarch_font-1.5.tar.gz"
license_take = ["README.stlarch"]
name = "STLarch"
form = "icon"
""",
        encoding="utf-8",
    )
    dest = tmp_path / "fonts"
    report = run_manifest(manifest, COLLECTION, dest)
    assert report.errors == []
    assert report.imported == ["stlarch"]
    assert (dest / "stlarch" / "stlarch.pcf").exists()
    readme = (dest / "stlarch" / "README.stlarch").read_text(encoding="utf-8")
    assert "GPLv2" in readme


def _mini_src(root, files):
    for rel, body in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")


def test_toml_escapes_control_characters(tmp_path):
    """说明文字里混进 \\r 之类控制字符时，生成的 family.toml 仍须能被解析。"""
    import tomllib

    src = tmp_path / "src" / "fam"
    _mini_src(src, {"a.bdf": "x"})
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[[family]]\nslug = "ctl"\nsource = "fam"\ntake = ["a.bdf"]\n'
        'name = "Ctl"\ndescription = "before\\rafter\\bmore\\ftail"\n',
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    report = run_manifest(manifest, tmp_path / "src", dest)
    assert report.errors == []
    text = (dest / "ctl" / "family.toml").read_text(encoding="utf-8")
    parsed = tomllib.loads(text)  # 会因裸控制字符抛异常
    assert parsed["description"] == "before\rafter\bmore\ftail"


def test_path_pattern_does_not_cross_directories(tmp_path):
    """“./*.bdf” 只能命中源目录根部，不得递归进子目录。"""
    src = tmp_path / "src" / "fam"
    _mini_src(src, {"top.bdf": "x", "nested/deep.bdf": "y"})
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[[family]]\nslug = "seg"\nsource = "fam"\ntake = ["./*.bdf"]\nname = "Seg"\n',
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    report = run_manifest(manifest, tmp_path / "src", dest)
    assert report.errors == []
    assert (dest / "seg" / "top.bdf").exists()
    assert not (dest / "seg" / "deep.bdf").exists()


def test_clash_detected_across_patterns(tmp_path):
    """两个模式各自命中一个同名文件时，后者会覆盖前者，必须报错。"""
    src = tmp_path / "src" / "fam"
    _mini_src(src, {"a/font.bdf": "x", "b/font.bdf": "y"})
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[[family]]\nslug = "clash"\nsource = "fam"\n'
        'take = ["a/font.bdf", "b/font.bdf"]\nname = "Clash"\n',
        encoding="utf-8",
    )
    report = run_manifest(manifest, tmp_path / "src", tmp_path / "out")
    assert any("font.bdf" in e and "多个来源" in e for e in report.errors), report.errors


def test_clash_detected_for_license_files(tmp_path):
    """license_files 只取排序第一个，同名多份时同样必须报错。"""
    src = tmp_path / "src" / "fam"
    _mini_src(src, {"f.bdf": "x", "a/LICENSE": "one", "b/LICENSE": "two"})
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[[family]]\nslug = "lic"\nsource = "fam"\ntake = ["f.bdf"]\n'
        'license_files = ["LICENSE"]\nname = "Lic"\n',
        encoding="utf-8",
    )
    report = run_manifest(manifest, tmp_path / "src", tmp_path / "out")
    assert any("LICENSE" in e and "多个来源" in e for e in report.errors), report.errors


def test_take_from_prefixes_destination_names(tmp_path):
    """上游按解析度分目录、文件名相同时，用 take_from 加前缀区分。"""
    src = tmp_path / "src" / "fam"
    _mini_src(src, {"a75/f12.bdf": "small", "a100/f12.bdf": "big"})
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[[family]]\nslug = "dpi"\nsource = "fam"\nname = "Dpi"\n\n'
        '[family.take_from]\n"75dpi-" = ["a75/*.bdf"]\n"100dpi-" = ["a100/*.bdf"]\n',
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    report = run_manifest(manifest, tmp_path / "src", dest)
    assert report.errors == []
    assert (dest / "dpi" / "75dpi-f12.bdf").read_text(encoding="utf-8") == "small"
    assert (dest / "dpi" / "100dpi-f12.bdf").read_text(encoding="utf-8") == "big"


def test_ppem_table_per_file(tmp_path):
    """同一家族含多个尺寸时，ppem 要能按文件名分别指定。"""
    import tomllib

    src = tmp_path / "src" / "fam"
    src.mkdir(parents=True)
    kh = Path("/home/chen/Downloads/fontsss/fonts/khdotfont-20150527")
    if not kh.exists():
        pytest.skip("KH dot font sources not available")
    for n in ("KH-Dot-Dougenzaka-12.ttf", "KH-Dot-Dougenzaka-16.ttf"):
        (src / n).write_bytes((kh / n).read_bytes())
    manifest = tmp_path / "m.toml"
    manifest.write_text(
        '[[family]]\nslug = "kh"\nsource = "fam"\nconvert = "ttf"\n'
        'convert_take = ["KH-Dot-Dougenzaka-*.ttf"]\nname = "KH"\n\n'
        '[family.ppem]\n"KH-Dot-Dougenzaka-12.ttf" = 12\n'
        '"KH-Dot-Dougenzaka-16.ttf" = 16\n',
        encoding="utf-8",
    )
    dest = tmp_path / "out"
    report = run_manifest(manifest, tmp_path / "src", dest)
    assert report.errors == []
    names = sorted(p.name for p in (dest / "kh").glob("*.bdf"))
    assert names == ["KH-Dot-Dougenzaka-12-12px.bdf", "KH-Dot-Dougenzaka-16-16px.bdf"]
    f = parse_bdf(dest / "kh" / "KH-Dot-Dougenzaka-12-12px.bdf", "kh")
    assert f.pixel_size == 12
    assert len(f.glyphs) > 7000
