import os
import shutil
from pathlib import Path

import pytest

from opf.ingest.uwttyp0 import build_all
from opf.parsers.bdf import parse_bdf


@pytest.mark.skipif(not (shutil.which("make") and shutil.which("sh")), reason="needs sh and make")
def test_uwttyp0_runs_upstream_build(tmp_path):
    """UW ttyp0 is built by upstream's own configure + make bdf in a scratch copy; genbdf/t0-*-uni.bdf become t0-*.bdf."""
    repo = tmp_path / "uw-ttyp0-9.9"
    (repo / "mgl").mkdir(parents=True)
    (repo / "mgl" / "unicode.mgl").write_text("PUT A 0x0041\n", encoding="latin-1")
    (repo / "configure").write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    (repo / "Makefile").write_text(
        'bdf:\n\ttest "$(GEN_BDF)" = 1\n\tmkdir -p genbdf\n\tcp master.bdf genbdf/t0-16-uni.bdf\n',
        encoding="utf-8",
    )
    (repo / "master.bdf").write_bytes((Path(__file__).parent / "fixtures" / "mini.bdf").read_bytes())
    dest = tmp_path / "fonts" / "uw-ttyp0"
    dest.mkdir(parents=True)
    (dest / "family.toml").write_text('name = "UW ttyp0"\n', encoding="utf-8")
    (dest / "t0-99.bdf").write_text("stale", encoding="utf-8")

    out = build_all(repo, dest)

    assert [name for name, _ in out] == ["t0-16.bdf"]
    assert not (dest / "t0-99.bdf").exists()
    assert (dest / "family.toml").exists()
    assert not (repo / "genbdf").exists()  # the source tree stays untouched
    f = parse_bdf(dest / "t0-16.bdf", "uw-ttyp0")
    assert 0x41 in {g.cp for g in f.glyphs}
    assert f.props["CHARSET_REGISTRY"] == "ISO10646"


def test_uwttyp0_official_release(tmp_path):
    """Opt-in: OPF_UWTTYP0 names an unpacked official release. Odd sizes must be complete fonts and COPYTO glyphs present."""
    repo = os.environ.get("OPF_UWTTYP0")
    if not repo:
        pytest.skip("set OPF_UWTTYP0 to an unpacked uw-ttyp0 release")
    dest = tmp_path / "uw-ttyp0"
    names = {name for name, _ in build_all(Path(repo), dest)}
    assert {"t0-11.bdf", "t0-16.bdf", "t0-22b.bdf"} <= names
    f = parse_bdf(dest / "t0-11.bdf", "uw-ttyp0")
    assert f.pixel_size == 11
    cps = {g.cp for g in f.glyphs}
    # U+002A and U+03AC only exist through COPYTO lines in unicode.mgl
    for cp in (0x2A, 0x41, 0xE9, 0x1EA0, 0x3AC, 0x2500):
        assert cp in cps, hex(cp)
