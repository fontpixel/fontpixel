import shutil
from pathlib import Path

from opf.licenses import LicenseInfo, detect_license
from opf.model import ParsedFont

FIX = Path(__file__).parent / "fixtures" / "licenses"


def _font(props: dict) -> ParsedFont:
    return ParsedFont(
        path=Path("x.bdf"), family_slug="x", file_name="x.bdf", props=props,
        pixel_size=16, ascent=14, descent=2, bbox=(16, 16, 0, -2),
        glyphs=[], warnings=[],
    )


def _dir_with(tmp_path: Path, name: str, fixture: str) -> Path:
    d = tmp_path / "fam"
    d.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIX / fixture, d / name)
    return d


def test_ofl11_auto_high(tmp_path):
    d = _dir_with(tmp_path, "OFL.txt", "ofl11.txt")
    li = detect_license(d, [_font({})], None)
    assert li.spdx == "OFL-1.1"
    assert li.confidence == "auto-high"
    assert li.file == "OFL.txt"


def test_mit_auto_high(tmp_path):
    d = _dir_with(tmp_path, "LICENSE", "mit.txt")
    li = detect_license(d, [_font({})], None)
    assert li.spdx == "MIT"


def test_gpl2_no_font_exception(tmp_path):
    d = _dir_with(tmp_path, "COPYING", "gpl2.txt")
    li = detect_license(d, [_font({})], None)
    assert li.spdx == "GPL-2.0-only"


def test_bsd2_and_ccby(tmp_path):
    d1 = _dir_with(tmp_path / "a", "LICENSE.txt", "bsd2.txt")
    assert detect_license(d1, [_font({})], None).spdx == "BSD-2-Clause"
    d2 = _dir_with(tmp_path / "b", "LICENSE.txt", "ccby4.txt")
    assert detect_license(d2, [_font({})], None).spdx == "CC-BY-4.0"


def test_dual_ofl_mit_prefers_ofl(tmp_path):
    d = tmp_path / "fam"
    d.mkdir()
    shutil.copy(FIX / "ofl11.txt", d / "LICENSE-OFL")
    shutil.copy(FIX / "mit.txt", d / "LICENSE-MIT")
    li = detect_license(d, [_font({})], None)
    assert li.spdx == "OFL-1.1"
    assert "MIT" in li.note


def test_props_hint_auto_low(tmp_path):
    d = tmp_path / "fam"
    d.mkdir()
    li = detect_license(
        d, [_font({"COPYRIGHT": "(c) X. Licensed under SIL Open Font License 1.1"})],
        None,
    )
    assert li.spdx == "OFL-1.1"
    assert li.confidence == "auto-low"


def test_unknown(tmp_path):
    d = tmp_path / "fam"
    d.mkdir()
    (d / "LICENSE.txt").write_text("You may use this font only on Tuesdays.")
    li = detect_license(d, [_font({})], None)
    assert li.spdx is None
    assert li.confidence == "unknown"


def test_manual_override_wins(tmp_path):
    d = _dir_with(tmp_path, "OFL.txt", "ofl11.txt")
    li = detect_license(
        d, [_font({})],
        {"spdx": "LicenseRef-Custom", "name": "自定义", "file": "OFL.txt",
         "note": "仅限个人"},
    )
    assert li == LicenseInfo(
        spdx="LicenseRef-Custom", name="自定义", file="OFL.txt",
        confidence="manual", note="仅限个人",
        name_en="自定义", note_en="",
    )


def test_manual_override_keeps_english_name():
    """The English UI must show the English license name; a manual override can supply name_en/note_en separately."""
    from pathlib import Path as _P

    li = detect_license(
        _P("/nonexistent"), [],
        {"spdx": "LicenseRef-PublicDomain", "name": "公有领域（東雲フォントライセンス）",
         "name_en": "Public Domain (Shinonome Font License)",
         "note": "中文说明", "note_en": "English note"},
    )
    assert li.name_en == "Public Domain (Shinonome Font License)"
    assert li.note_en == "English note"
    assert li.name == "公有领域（東雲フォントライセンス）"

