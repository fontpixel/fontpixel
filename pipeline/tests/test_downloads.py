import gzip
import hashlib
import shutil
import zipfile
from pathlib import Path

import pytest

from opf.downloads import build_downloads
from opf.familymeta import FamilyMeta, resolve_variant
from opf.parsers.bdf import parse_bdf

FIX = Path(__file__).parent / "fixtures"
HAVE_BDFTOPCF = shutil.which("bdftopcf") is not None


def _family(tmp_path: Path) -> Path:
    d = tmp_path / "mini"
    d.mkdir()
    shutil.copy(FIX / "mini.bdf", d / "mini.bdf")
    shutil.copy(FIX / "licenses" / "ofl11.txt", d / "OFL.txt")
    return d


def _fonts(d: Path):
    f = parse_bdf(d / "mini.bdf", "mini")
    v = resolve_variant(f, FamilyMeta(slug="mini", name="Mini"))
    return [(f, v)]


def test_build_downloads_outputs(tmp_path):
    d = _family(tmp_path)
    out = tmp_path / "dl"
    entries = build_downloads("mini", d, _fonts(d), ["OFL.txt"],
                              "来源:测试\n", out)
    kinds = {e["kind"] for e in entries}
    assert "bdf" in kinds and "zip" in kinds and "ttf" in kinds
    if HAVE_BDFTOPCF:
        assert "pcf" in kinds
    for e in entries:
        p = out / e["file"]
        assert p.exists()
        assert e["bytes"] == p.stat().st_size
        assert e["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()

    bdf_entry = next(e for e in entries if e["kind"] == "bdf")
    raw = gzip.decompress((out / bdf_entry["file"]).read_bytes())
    assert raw == (d / "mini.bdf").read_bytes()

    with zipfile.ZipFile(out / "mini.zip") as z:
        names = set(z.namelist())
        assert "mini.bdf" in names
        assert "OFL.txt" in names
        assert "README.txt" in names
        assert "来源:测试" in z.read("README.txt").decode("utf-8")


def test_ttf_bundles_all_sizes(tmp_path):
    """Multiple sizes of the same font should merge into one bitmap TTF."""
    from opf.ingest.otb import convert_otb

    d = _family(tmp_path)
    shutil.copy(FIX / "real-galmuri7.bdf", d / "small.bdf")
    out = tmp_path / "dl"
    entries = build_downloads("mini", d, _fonts_multi(d), ["OFL.txt"], "r", out)
    ttfs = [e for e in entries if e["kind"] == "ttf"]
    assert len(ttfs) == 1, "同字重同排布应只出一个 TTF"
    expected = {f"{f.pixel_size}px" for f, _ in _fonts_multi(d)}
    assert len(expected) == 2
    strikes = convert_otb(out / ttfs[0]["file"], "mini")
    assert len(strikes) == 2, "两个尺寸应各成一个 strike"
    assert {s for s, _ in strikes} == expected


def _fonts_multi(d):
    from opf.familymeta import FamilyMeta, resolve_variant
    from opf.parsers.bdf import parse_bdf as _p

    meta = FamilyMeta(slug="mini", name="Mini")
    out = []
    for name in ("mini.bdf", "small.bdf"):
        f = _p(d / name, "mini")
        v = resolve_variant(f, meta)
        v.weight, v.spacing, v.script_subset = "regular", "proportional", None
        out.append((f, v))
    return out


def test_deterministic(tmp_path):
    d = _family(tmp_path)
    o1, o2 = tmp_path / "a", tmp_path / "b"
    build_downloads("mini", d, _fonts(d), ["OFL.txt"], "r", o1)
    build_downloads("mini", d, _fonts(d), ["OFL.txt"], "r", o2)
    for p1 in sorted(o1.iterdir()):
        assert p1.read_bytes() == (o2 / p1.name).read_bytes(), p1.name


@pytest.mark.skipif(not HAVE_BDFTOPCF, reason="bdftopcf missing")
def test_pcf_roundtrip(tmp_path):
    from opf.parsers.pcf import parse_pcf

    d = _family(tmp_path)
    out = tmp_path / "dl"
    entries = build_downloads("mini", d, _fonts(d), ["OFL.txt"], "r", out)
    pcf_entry = next(e for e in entries if e["kind"] == "pcf")
    raw = gzip.decompress((out / pcf_entry["file"]).read_bytes())
    tmp = tmp_path / "x.pcf"
    tmp.write_bytes(raw)
    pf = parse_pcf(tmp, "mini")
    assert len(pf.glyphs) == 2


def test_write_bdf_roundtrip(tmp_path):
    from opf.ingest.bdfwrite import write_bdf

    f = parse_bdf(FIX / "mini.bdf", "mini")
    out = tmp_path / "rt.bdf"
    write_bdf(f, out)
    f2 = parse_bdf(out, "mini")
    assert len(f2.glyphs) == len(f.glyphs)
    for a, b in zip(f.glyphs, f2.glyphs):
        assert (a.cp, a.dwidth, a.bbw, a.bbh, a.bbx, a.bby) == (
            b.cp, b.dwidth, b.bbw, b.bbh, b.bbx, b.bby)
        assert a.rows == b.rows
    assert f2.pixel_size == f.pixel_size
    assert f2.ascent == f.ascent


def test_metadata_refresh_matches_a_full_rebuild_byte_for_byte(tmp_path):
    """The TTF/zip produced by the fast path must be byte-identical to a full rebuild with new metadata.

    The output's sha256 gets published on the download page. If the two paths
    produced different bytes, the same font's checksum would depend on which path
    it happened to take -- which would make this optimization unusable.
    """
    from opf.downloads import refresh_downloads_metadata

    fam = _family(tmp_path)
    fonts = _fonts(fam)

    old_out = tmp_path / "old"
    entries = build_downloads("mini", fam, fonts, ["OFL.txt"], "旧 README\n",
                              old_out, family_display="Mini",
                              copyright_line="Mini — 旧作者")

    # control group: rebuild fully with the new metadata directly
    want_out = tmp_path / "want"
    want = build_downloads("mini", fam, _fonts(fam), ["OFL.txt"], "新 README\n",
                           want_out, family_display="Mini",
                           copyright_line="Mini — 新作者（handle）")

    # fast path: only refresh the new metadata onto the existing output
    got = refresh_downloads_metadata(entries, old_out, "新 README\n",
                                     "Mini", "Mini — 新作者（handle）")

    assert [e["file"] for e in got] == [e["file"] for e in want]
    for g, w in zip(got, want):
        assert g["sha256"] == w["sha256"], f"{g['file']} 字节不一致"
        assert (old_out / g["file"]).read_bytes() == (want_out / w["file"]).read_bytes()


def test_metadata_refresh_gives_up_when_outputs_are_gone(tmp_path):
    # when output files are gone, must fall back to a full rebuild rather than silently handing out a half-formed download
    from opf.downloads import refresh_downloads_metadata

    fam = _family(tmp_path)
    out = tmp_path / "out"
    entries = build_downloads("mini", fam, _fonts(fam), ["OFL.txt"],
                              "README\n", out, family_display="Mini")
    (out / entries[0]["file"]).unlink()
    assert refresh_downloads_metadata(entries, out, "README\n", "Fam", "c") == []
