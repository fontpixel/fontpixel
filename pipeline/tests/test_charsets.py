from pathlib import Path

from pfc.coverage.charsets import DATA_DIR, load_charsets
from pfc.coverage.ucd import load_ucd


def _by_id():
    return {c.id: c for c in load_charsets(DATA_DIR)}


def test_known_counts_codec_derived():
    cs = _by_id()
    assert len(cs["gb2312-l1"].cps) == 3755
    assert len(cs["gb2312-l2"].cps) == 3008
    assert len(cs["big5-changyong"].cps) == 5401
    assert len(cs["ksx1001-hangul"].cps) == 2350
    assert len(cs["ksx1001-hanja"].cps) == 4888
    assert len(cs["jisx0208-l1"].cps) == 2965
    assert len(cs["jisx0208-l2"].cps) == 3390
    assert len(cs["hangul-syllables"].cps) == 11172


def test_known_counts_static():
    cs = _by_id()
    assert len(cs["hiragana"].cps) == 86  # U+3041..3096
    assert len(cs["katakana"].cps) == 90  # U+30A1..30FA
    assert len(cs["kangxi-radicals"].cps) == 214
    assert len(cs["cp437"].cps) == 255  # 图形解释 0x01–0xFF,0x00 不算字形
    assert len(cs["box-drawing"].cps) == 128
    assert len(cs["braille"].cps) == 256
    assert len(cs["halfwidth-kana"].cps) == 63
    assert len(cs["powerline"].cps) == 41


def test_migrated_tables():
    cs = _by_id()
    assert len(cs["iicore"].cps) == 9810
    assert len(cs["tongyong-guifan"].cps) == 8105
    assert len(cs["tw-changyong-4808"].cps) == 4808
    assert len(cs["hkscs"].cps) == 4603
    assert "香港" in cs["hkscs"].name_zh or "HKSCS" in cs["hkscs"].name_zh


def test_task5_external_tables():
    cs = _by_id()
    assert len(cs["tongyong-guifan-l1"].cps) == 3500
    assert len(cs["tongyong-guifan-l2"].cps) == 3000
    assert len(cs["tongyong-guifan-l3"].cps) == 1605
    union = cs["tongyong-guifan-l1"].cps | cs["tongyong-guifan-l2"].cps | cs[
        "tongyong-guifan-l3"].cps
    assert union == cs["tongyong-guifan"].cps
    assert len(cs["joyo"].cps) == 2136
    assert len(cs["kyoiku"].cps) == 1026
    assert cs["kyoiku"].cps <= cs["joyo"].cps
    assert len(cs["jinmeiyo"].cps) == 864
    assert len(cs["wgl4"].cps) == 650
    for cp in (0x20, 0xC5, 0x152, 0x2122, 0x25CA, 0xFB01, 0xFB02):
        assert cp in cs["wgl4"].cps
    assert len(cs["unihan-core-2020"].cps) == 20720
    assert len(cs["viet-latin"].cps) == 186
    assert len(cs["changyong-2500"].cps) == 2500
    assert len(cs["cichangyong-1000"].cps) == 1000
    assert (cs["changyong-2500"].cps | cs["cichangyong-1000"].cps
            ) == cs["changyong-3500"].cps


def test_gb18030_2022_levels():
    cs = _by_id()
    l1, l2, l3 = (cs[f"gb18030-2022-l{i}"].cps for i in (1, 2, 3))
    assert (len(l1), len(l2), len(l3)) == (27584, 27780, 88115)
    assert l1 < l2 < l3  # 严格包含
    assert cs["tongyong-guifan"].cps <= l2


def test_sections_valid():
    valid = {"gb", "prc-lit", "tw", "hk", "jp", "kr", "intl"}
    for c in load_charsets(DATA_DIR):
        assert c.section in valid, c.id


def test_every_table_has_metadata():
    for c in load_charsets(DATA_DIR):
        assert c.name_zh, c.id
        assert c.name_en, c.id
        assert c.source, c.id
        assert len(c.cps) > 0, c.id


def test_loader_formats(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    (d / "t.txt").write_text(
        "# id: t\n# section: intl\n# name_zh: 测试\n# name_en: Test\n"
        "# source: unit test\n# order: 1\n"
        "0041\n0043..0045\n汉字\n",
        encoding="utf-8",
    )
    (cs,) = load_charsets(tmp_path)
    assert cs.cps == frozenset({0x41, 0x43, 0x44, 0x45, ord("汉"), ord("字")})


def test_ucd_blocks():
    u = load_ucd(DATA_DIR / "ucd")
    assert ("Basic Latin", 0x0000, 0x007F) in u.blocks
    assert u.block_assigned_counts["Basic Latin"] == 128
    assert 0x4E00 in u.assigned
    assert 0xD800 not in u.assigned  # 代理区不算字符
    # PUA 属已指派(Co)
    assert 0xE000 in u.assigned
    names = [b[0] for b in u.blocks]
    assert "CJK Unified Ideographs Extension J" in names  # Unicode 17.0
