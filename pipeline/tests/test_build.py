import json
import shutil
from pathlib import Path

from pfc.build import build

FIX = Path(__file__).parent / "fixtures"


def _setup(tmp_path: Path):
    fonts = tmp_path / "fonts"
    shutil.copytree(FIX / "fonts-tree", fonts)
    return fonts, tmp_path / "data", tmp_path / "dl", tmp_path / "cache"


def test_full_build(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    report = build(fonts, data, dl, cache)
    assert report.families == 2
    assert report.cached == 0

    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    fams = {f["slug"]: f for f in idx["families"]}
    assert set(fams) == {"mini", "nometa"}

    mini = fams["mini"]
    assert mini["name"] == "Mini Test"
    assert mini["nameZh"] == "迷你测试"
    assert mini["form"] == "gothic"
    assert mini["curated"] is True
    assert mini["license"]["spdx"] == "OFL-1.1"
    assert mini["license"]["confidence"] == "auto-high"
    assert mini["sizes"] == [16]
    assert len(mini["variants"]) == 2  # mini.bdf + mini2.bdf.gz
    assert mini["added"] == "2026-08-21"

    nometa = fams["nometa"]
    assert nometa["curated"] is False
    assert (fonts / "nometa" / "family.toml").exists()  # stub 已写

    # 逐变体资产
    for v in mini["variants"]:
        vdir = data / "packs" / "mini" / v["id"]
        assert (vdir / "manifest.json").exists()
        assert (vdir / "core.bin.gz").exists()
    assert (data / "og" / "mini.png").exists()
    previews = list((data / "previews" / "mini").glob("*.svg"))
    assert previews, "至少一个预渲染 SVG"

    detail = json.loads((data / "details" / "mini.json").read_text(encoding="utf-8"))
    first_variant = mini["variants"][0]["id"]
    assert detail["coverage"][first_variant]["gb2312"][1] == 6763
    assert detail["metrics"][first_variant]["pixelSize"] == 16
    assert detail["overview"][first_variant]["total"][0] == 2
    assert any(b[0] == "Basic Latin" for b in detail["unicodeBlocks"][first_variant])
    assert detail["licenseText"] == "OFL.txt"

    dlm = json.loads((dl / "manifest.json").read_text(encoding="utf-8"))
    kinds = {(e["family"], e["kind"]) for e in dlm["entries"]}
    assert ("mini", "bdf") in kinds and ("mini", "zip") in kinds


def test_incremental_cache(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    idx1 = (data / "index.json").read_bytes()
    report2 = build(fonts, data, dl, cache)
    assert report2.cached == 2
    assert (data / "index.json").read_bytes() == idx1

    # 修改 toml → 只重建该家族
    toml = fonts / "mini" / "family.toml"
    toml.write_text(toml.read_text().replace("迷你测试", "迷你测试2"), encoding="utf-8")
    report3 = build(fonts, data, dl, cache)
    assert report3.cached == 1
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert {f["slug"]: f for f in idx["families"]}["mini"]["nameZh"] == "迷你测试2"


def test_only_family(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    report = build(fonts, data, dl, cache, only_family="mini")
    assert report.families == 1
    assert not (data / "details" / "nometa.json").exists()


def test_variant_id_collision_uniquified(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    # mini.bdf 与 mini.bdf.gz 同名 → id 冲突,应加后缀并告警
    shutil.copy(FIX / "fonts-tree" / "mini" / "mini2.bdf.gz",
                fonts / "mini" / "mini.bdf.gz")
    report = build(fonts, data, dl, cache, only_family="mini")
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    ids = [v["id"] for f in idx["families"] for v in f["variants"]]
    assert len(ids) == len(set(ids))
    assert any("collision" in w or "冲突" in w for w in report.warnings)
