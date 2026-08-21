import gzip
import hashlib
import shutil
import zipfile
from pathlib import Path

import pytest

from pfc.downloads import build_downloads
from pfc.familymeta import FamilyMeta, resolve_variant
from pfc.parsers.bdf import parse_bdf

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
    assert "bdf" in kinds and "zip" in kinds
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


def test_deterministic(tmp_path):
    d = _family(tmp_path)
    o1, o2 = tmp_path / "a", tmp_path / "b"
    build_downloads("mini", d, _fonts(d), ["OFL.txt"], "r", o1)
    build_downloads("mini", d, _fonts(d), ["OFL.txt"], "r", o2)
    for p1 in sorted(o1.iterdir()):
        assert p1.read_bytes() == (o2 / p1.name).read_bytes(), p1.name


@pytest.mark.skipif(not HAVE_BDFTOPCF, reason="bdftopcf missing")
def test_pcf_roundtrip(tmp_path):
    from pfc.parsers.pcf import parse_pcf

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
    from pfc.ingest.bdfwrite import write_bdf

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
