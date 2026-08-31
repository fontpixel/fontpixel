from pathlib import Path

from opf.coverage.charsets import DATA_DIR, load_charsets
from opf.coverage.engine import (
    badges,
    coverage_for,
    detect_scripts,
    font_cps,
    overview,
    pick_sample_lang,
    unicode_block_coverage,
)
from opf.coverage.ucd import load_ucd
from opf.model import Glyph, ParsedFont

CHARSETS = load_charsets(DATA_DIR)
UCD = load_ucd(DATA_DIR / "ucd")
BY_ID = {c.id: c for c in CHARSETS}


def _font(cps: set[int]) -> ParsedFont:
    return ParsedFont(
        path=Path("x.bdf"), family_slug="x", file_name="x.bdf", props={},
        pixel_size=16, ascent=14, descent=2, bbox=(16, 16, 0, -2),
        glyphs=[
            Glyph(cp=cp, name=f"u{cp:x}", dwidth=8, bbw=1, bbh=1, bbx=0, bby=0,
                  rows=b"\x80")
            for cp in sorted(cps)
        ],
        warnings=[],
    )


def test_font_cps():
    assert font_cps(_font({65, 0x4E00})) == frozenset({65, 0x4E00})


def test_coverage_full_and_partial():
    full = BY_ID["gb2312-l1"].cps
    cov = coverage_for(frozenset(full), CHARSETS)
    assert cov["gb2312-l1"] == (3755, 3755)
    half = frozenset(sorted(full)[:1000])
    cov2 = coverage_for(half, CHARSETS)
    assert cov2["gb2312-l1"] == (1000, 3755)


def test_badges():
    cov = coverage_for(frozenset(BY_ID["gb2312"].cps), CHARSETS)
    assert "gb2312" in badges(cov)
    kana = BY_ID["hiragana"].cps | BY_ID["katakana"].cps
    assert "kana" in badges(coverage_for(frozenset(kana), CHARSETS))
    assert badges(coverage_for(frozenset({65}), CHARSETS)) == []


def test_detect_scripts_and_sample_lang():
    # Simplified Chinese needs the full GB/T 2312 (>=90%); level-1 alone isn't enough
    cov = coverage_for(frozenset(BY_ID["gb2312"].cps), CHARSETS)
    assert "zh-hans" in detect_scripts(cov)
    assert pick_sample_lang(cov) == "zh-Hans"
    partial = coverage_for(frozenset(BY_ID["gb2312-l1"].cps), CHARSETS)
    assert "zh-hans" not in detect_scripts(partial), "一级字表仅占 55%，不该算简体中文"

    kana_only = coverage_for(
        frozenset(BY_ID["hiragana"].cps | BY_ID["katakana"].cps), CHARSETS
    )
    assert "ja" not in detect_scripts(kana_only), "只有假名没有汉字不算日文"
    ja_cov = coverage_for(
        frozenset(BY_ID["hiragana"].cps | BY_ID["katakana"].cps
                  | BY_ID["jisx0208-l1"].cps), CHARSETS
    )
    assert "ja" in detect_scripts(ja_cov)
    assert pick_sample_lang(ja_cov) == "ja"
    latin_cov = coverage_for(frozenset(range(0x20, 0x7F)), CHARSETS)
    assert detect_scripts(latin_cov) == ["latin"]
    assert pick_sample_lang(latin_cov) == "latin"


def test_pan_cjk_font_prefers_zh_hans_sample():
    """WQY-style font: full GB2312 coverage plus high kana/JIS -> sample should be zh-Hans, not ja."""
    cps = set(BY_ID["gb2312"].cps) | set(BY_ID["hiragana"].cps) | set(
        BY_ID["katakana"].cps)
    cps |= set(sorted(BY_ID["jisx0208-l1"].cps)[:2800])  # jis1 ~0.94
    cov = coverage_for(frozenset(cps), CHARSETS)
    assert pick_sample_lang(cov) == "zh-Hans"


def test_korean_font_prefers_ko_sample():
    cps = set(BY_ID["ksx1001-hangul"].cps) | set(BY_ID["hiragana"].cps) | set(
        BY_ID["katakana"].cps) | set(range(0x20, 0x7F))
    # Fonts like Baekmuk, a Korean font family, carry some hanja but must not be flagged as Chinese
    cov = coverage_for(frozenset(cps), CHARSETS)
    assert pick_sample_lang(cov) == "ko"


def test_overview():
    ov = overview(frozenset({0x41, 0x4E00, 0xE000, 0xFA0E, 0x20000}), UCD)
    assert ov["total"][0] == 5
    assert ov["total"][1] == len(UCD.assigned)
    planes = dict((p[0], (p[1], p[2])) for p in ov["planes"])
    assert planes["BMP"][0] == 4
    assert planes["SIP"][0] == 1
    pua = dict((p[0], (p[1], p[2])) for p in ov["pua"])
    assert pua["BMP PUA"] == (1, 6400)
    assert pua["Plane 15"] == (0, 65534)
    assert ov["han_total"][0] == 2  # 4E00 + 20000; FA0E is counted separately under the compatibility block
    assert ov["compat"][0] == 1
    assert ov["compat_unified_note"] == (1, 12)


def test_unicode_block_coverage():
    rows = unicode_block_coverage(frozenset({0x41}), UCD)
    d = {r[0]: (r[1], r[2]) for r in rows}
    assert d["Basic Latin"] == (1, 128)
    assert len(rows) > 100  # includes zero-coverage blocks (every assigned block is listed)
    assert d["CJK Unified Ideographs"][0] == 0
