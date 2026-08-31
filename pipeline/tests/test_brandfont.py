import json
import shutil
from pathlib import Path

import opf.brandfont as bf
from opf.parsers.bdf import parse_bdf

FIX = Path(__file__).parent / "fixtures"


def _setup(tmp_path, monkeypatch):
    fonts = tmp_path / "fonts"
    shutil.copytree(FIX / "fonts-tree", fonts)
    monkeypatch.setattr(bf, "SOURCES", ("mini/mini.bdf",))
    cps = sorted(g.cp for g in parse_bdf(fonts / "mini" / "mini.bdf", "mini").glyphs)
    text = "".join(chr(c) for c in cps[:5])
    names = tmp_path / "sitenames.json"
    names.write_text(json.dumps({"zh": text, "en": text}), encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    return fonts, data, names, text


def test_subset_covers_the_brand_text_and_nothing_else(tmp_path, monkeypatch):
    fonts, data, names, text = _setup(tmp_path, monkeypatch)
    meta = bf.build_brand_font(fonts, data, names)
    assert (data / meta["file"]).exists()
    assert meta["family"] == "FBF Brand"      # OFL 保留字体名条款：子集必须改名

    from fontTools.ttLib import TTFont
    f = TTFont(data / meta["file"])
    cmap = f.getBestCmap()
    assert set(cmap) == {ord(c) for c in text}
    assert f["name"].getDebugName(1) == "FBF Brand"


def test_output_is_deterministic(tmp_path, monkeypatch):
    fonts, data, names, _ = _setup(tmp_path, monkeypatch)
    meta = bf.build_brand_font(fonts, data, names)
    first = (data / meta["file"]).read_bytes()
    meta2 = bf.build_brand_font(fonts, data, names)
    assert (data / meta2["file"]).read_bytes() == first
