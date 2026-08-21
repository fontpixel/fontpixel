import gzip
import shutil
from pathlib import Path

from pfc.parsers.bdf import parse_bdf

FIX = Path(__file__).parent / "fixtures"


def test_parse_mini_bdf():
    f = parse_bdf(FIX / "mini.bdf", "mini")
    assert f.family_slug == "mini"
    assert f.file_name == "mini.bdf"
    assert f.pixel_size == 16
    assert f.ascent == 14
    assert f.descent == 2
    assert f.bbox == (16, 16, 0, -2)
    assert [g.cp for g in f.glyphs] == [65, 27704]  # ENCODING -1 被跳过,升序
    a = f.glyphs[0]
    assert (a.name, a.dwidth, a.bbw, a.bbh, a.bbx, a.bby) == ("A", 8, 7, 10, 0, 0)
    assert len(a.rows) == 10 * 1  # ceil(7/8) == 1
    assert a.rows[0] == 0x30
    assert a.rows[5] == 0xFC
    yong = f.glyphs[1]
    assert (yong.dwidth, yong.bbw, yong.bbh, yong.bbx, yong.bby) == (16, 16, 15, 0, -1)
    assert len(yong.rows) == 15 * 2
    assert f.props["FOUNDRY"] == "test"
    assert f.props["PIXEL_SIZE"] == 16


def test_parse_gz(tmp_path):
    gz = tmp_path / "mini.bdf.gz"
    with open(FIX / "mini.bdf", "rb") as s, gzip.open(gz, "wb") as d:
        shutil.copyfileobj(s, d)
    f = parse_bdf(gz, "mini")
    assert len(f.glyphs) == 2
    assert f.file_name == "mini.bdf.gz"


def test_bad_bitmap_lines_warn():
    f = parse_bdf(FIX / "mini-bad.bdf", "mini")
    assert len(f.glyphs) == 1
    g = f.glyphs[0]
    assert len(g.rows) == 3  # 每行强制归一到 1 字节
    assert any("bitmap" in w.lower() for w in f.warnings)


def test_missing_ascent_derived(tmp_path):
    src = (FIX / "mini.bdf").read_text()
    src = src.replace("FONT_ASCENT 14\n", "").replace("FONT_DESCENT 2\n", "")
    src = src.replace("STARTPROPERTIES 5", "STARTPROPERTIES 3")
    p = tmp_path / "noasc.bdf"
    p.write_text(src)
    f = parse_bdf(p, "mini")
    # 从 FONTBOUNDINGBOX 16 16 0 -2 推导:ascent = h + yoff = 14, descent = 2
    assert f.ascent == 14
    assert f.descent == 2
    assert any("ascent" in w.lower() for w in f.warnings)


def test_missing_dwidth_falls_back_to_fbb_width(tmp_path):
    """UnifontEX 式方言:全宽字形省略 DWIDTH → 用 FONTBOUNDINGBOX 宽度。"""
    src = (FIX / "mini.bdf").read_text()
    src = src.replace("ENCODING 27704\nSWIDTH 1000 0\nDWIDTH 16 0\n",
                      "ENCODING 27704\n")
    p = tmp_path / "nodw.bdf"
    p.write_text(src)
    f = parse_bdf(p, "x")
    yong = next(g for g in f.glyphs if g.cp == 27704)
    assert yong.dwidth == 16  # FONTBOUNDINGBOX 16 16 0 -2
    a = next(g for g in f.glyphs if g.cp == 65)
    assert a.dwidth == 8  # 显式 DWIDTH 不受影响
    assert any("DWIDTH" in w for w in f.warnings)


def test_ksx_registry_remapped_to_unicode():
    """baekmuk batang:ksx1001.1997 GL 编码的 BDF 应重映射到 Unicode。"""
    f = parse_bdf(FIX / "real-batang10-ksx.bdf", "batang")
    cps = {g.cp for g in f.glyphs}
    assert 0xAC00 in cps  # 가
    assert 0x6C38 in cps  # 永(KS 汉字区)
    assert 0xB2E4 in cps  # 다
    hangul = sum(1 for cp in cps if 0xAC00 <= cp <= 0xD7A3)
    assert hangul >= 2300  # KS X 1001 谚文 2350 应几乎全数映射
    assert len(cps) > 8000
    assert any("unmappable" in w for w in f.warnings)  # KS 特殊行无对应,预期丢弃


def test_real_galmuri7():
    f = parse_bdf(FIX / "real-galmuri7.bdf", "galmuri7")
    assert len(f.glyphs) > 1000
    cps = [g.cp for g in f.glyphs]
    assert cps == sorted(cps)
    assert len(cps) == len(set(cps))
    from pfc.model import row_bytes

    for g in f.glyphs:
        assert len(g.rows) == g.bbh * row_bytes(g.bbw)
