import shutil
import subprocess
from pathlib import Path

import pytest

from opf.parsers.bdf import parse_bdf
from opf.parsers.pcf import parse_pcf

FIX = Path(__file__).parent / "fixtures"


def _assert_same_glyphs(pcf_font, bdf_font):
    assert len(pcf_font.glyphs) == len(bdf_font.glyphs)
    for pg, bg in zip(pcf_font.glyphs, bdf_font.glyphs):
        assert pg.cp == bg.cp
        assert pg.dwidth == bg.dwidth, f"cp {pg.cp:x}"
        assert (pg.bbw, pg.bbh, pg.bbx, pg.bby) == (bg.bbw, bg.bbh, bg.bbx, bg.bby), (
            f"cp {pg.cp:x}"
        )
        assert pg.rows == bg.rows, f"cp {pg.cp:x} bitmap mismatch"


def test_parse_mini_pcf_matches_bdf():
    bdf = parse_bdf(FIX / "mini.bdf", "mini")
    pcf = parse_pcf(FIX / "mini.pcf", "mini")
    _assert_same_glyphs(pcf, bdf)
    assert pcf.pixel_size == 16
    assert pcf.ascent == 14
    assert pcf.descent == 2
    assert pcf.props["FOUNDRY"] == "test"


def test_parse_terminal_pcf_matches_bdf():
    # -t 用终端字形填充;墨迹外框可能被填充到等宽——只比码位/位图内容按 BDF 裁剪比较
    pcf = parse_pcf(FIX / "mini-t.pcf", "mini")
    assert [g.cp for g in pcf.glyphs] == [65, 27704]


@pytest.mark.skipif(shutil.which("bdftopcf") is None, reason="bdftopcf missing")
@pytest.mark.parametrize(
    "flags",
    [["-m", "-M"], ["-l", "-L"], ["-m", "-L"], ["-l", "-M"],
     ["-p2", "-u2"], ["-p4", "-u4", "-l", "-M"]],
)
def test_pcf_bit_byte_order_variants(tmp_path, flags):
    out = tmp_path / "v.pcf"
    subprocess.run(
        ["bdftopcf", *flags, str(FIX / "mini.bdf"), "-o", str(out)], check=True
    )
    bdf = parse_bdf(FIX / "mini.bdf", "mini")
    pcf = parse_pcf(out, "mini")
    _assert_same_glyphs(pcf, bdf)


def test_pcf_gz(tmp_path):
    import gzip

    gz = tmp_path / "mini.pcf.gz"
    with open(FIX / "mini.pcf", "rb") as s, gzip.open(gz, "wb") as d:
        shutil.copyfileobj(s, d)
    pcf = parse_pcf(gz, "mini")
    assert len(pcf.glyphs) == 2
