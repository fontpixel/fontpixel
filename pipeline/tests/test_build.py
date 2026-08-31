import json
import shutil
from pathlib import Path

from opf.build import build

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
    assert mini["names"] == {"zh-Hans": "迷你测试"}
    assert mini["form"] == "gothic"
    assert mini["curated"] is True
    assert mini["license"]["spdx"] == "OFL-1.1"
    assert mini["license"]["confidence"] == "auto-high"
    assert mini["sizes"] == [16]
    assert len(mini["variants"]) == 2  # mini.bdf + mini2.bdf.gz
    assert mini["added"] == "2026-08-21"

    # Former names/aliases feed into search text; Chinese aliases get Simplified/Traditional expansion like the family name
    assert "MiniOld" in mini["searchText"]
    assert "迷你旧名" in mini["searchText"]
    assert "舊" in mini["searchText"]
    # Co-authors are passed through as-is; the frontend turns each into a per-author search link
    assert mini["authors"] == ["PFC Tests", "Second Author"]
    assert mini["authorsEn"] == ["PFC Tests", "Second Author"]

    nometa = fams["nometa"]
    assert nometa["curated"] is False
    assert (fonts / "nometa" / "family.toml").exists()  # stub was written

    # Per-variant assets
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

    assert "SIL OPEN FONT LICENSE" in (
        data / "licenses" / "mini.txt"
    ).read_text(encoding="utf-8", errors="replace")

    dlm = json.loads((dl / "manifest.json").read_text(encoding="utf-8"))
    kinds = {(e["family"], e["kind"]) for e in dlm["entries"]}
    assert ("mini", "bdf") in kinds and ("mini", "zip") in kinds


def test_coverage_intervals_and_missing(tmp_path):
    from opf.emit import read_intervals

    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)

    runs = read_intervals(data / "coverage-intervals.bin.gz")
    assert set(runs) == {"mini", "nometa"}
    assert runs["mini"] == [(65, 66), (27704, 27705)]

    detail = json.loads((data / "details" / "mini.json").read_text(encoding="utf-8"))
    vid = detail["meta"]["variants"][0]["id"]
    # hiragana has 86 chars total, mini is missing all of them (<=500) -> a missing-chars list is provided
    assert len(detail["missingChars"][vid]["hiragana"]) == 86
    # gb2312 is missing 6763 chars (>500) -> not provided
    assert "gb2312" not in detail["missingChars"][vid]

    charsets = json.loads((data / "charsets.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in charsets["charsets"]}
    assert by_id["gb2312"]["nameZh"].startswith("GB/T 2312")
    assert by_id["gb2312"]["total"] == 6763
    assert by_id["gb2312"]["section"] == "gb"
    assert charsets["sections"][0] == "gb"

    # After a cached rerun, intervals are still complete (sourced from the cache payload)
    build(fonts, data, dl, cache)
    runs2 = read_intervals(data / "coverage-intervals.bin.gz")
    assert runs2 == runs


def test_incremental_cache(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    idx1 = (data / "index.json").read_bytes()
    report2 = build(fonts, data, dl, cache)
    assert report2.cached == 2
    assert (data / "index.json").read_bytes() == idx1

    # Modify a structural field -> only that family is rebuilt (localized names are descriptive and take the fast path, tested separately)
    toml = fonts / "mini" / "family.toml"
    toml.write_text(toml.read_text().replace('name = "Mini Test"', 'name = "Mini Test 2"'),
                    encoding="utf-8")
    report3 = build(fonts, data, dl, cache)
    assert report3.cached == 1
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert {f["slug"]: f for f in idx["families"]}["mini"]["name"] == "Mini Test 2"


def test_broken_family_isolated(tmp_path):
    """A broken family.toml in one family should not take down the whole build."""
    fonts, data, dl, cache = _setup(tmp_path)
    (fonts / "mini" / "family.toml").write_text("这不是合法的 TOML ===", encoding="utf-8")
    report = build(fonts, data, dl, cache)
    assert report.failed == 1
    assert any("mini" in w and "失败" in w for w in report.warnings)
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert [f["slug"] for f in idx["families"]] == ["nometa"]  # other families are unaffected


def test_orphan_outputs_pruned(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    assert (data / "details" / "nometa.json").exists()
    shutil.rmtree(fonts / "nometa")
    build(fonts, data, dl, cache)
    assert not (data / "details" / "nometa.json").exists()
    assert not (data / "packs" / "nometa").exists()
    assert not (data / "og" / "nometa.png").exists()
    dlm = json.loads((dl / "manifest.json").read_text(encoding="utf-8"))
    assert all(e["family"] != "nometa" for e in dlm["entries"])
    assert not list(dl.glob("nometa*"))
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert [f["slug"] for f in idx["families"]] == ["mini"]


def test_only_family(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    report = build(fonts, data, dl, cache, only_family="mini")
    assert report.families == 1
    assert not (data / "details" / "nometa.json").exists()


def test_variant_id_collision_uniquified(tmp_path):
    fonts, data, dl, cache = _setup(tmp_path)
    # mini.bdf and mini.bdf.gz share a name -> id collision, should get a suffix and a warning
    shutil.copy(FIX / "fonts-tree" / "mini" / "mini2.bdf.gz",
                fonts / "mini" / "mini.bdf.gz")
    report = build(fonts, data, dl, cache, only_family="mini")
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    ids = [v["id"] for f in idx["families"] for v in f["variants"]]
    assert len(ids) == len(set(ids))
    assert any("collision" in w or "冲突" in w for w in report.warnings)


def test_ts_fixtures_in_sync(tmp_path):
    """The site's zod contract fixtures must match the pipeline's real output.

    The fixtures are copied by hand; changing the index/detail structure lets them
    silently go stale until vitest fails on the site side. This compares against
    the actual build output directly; to update, run OPF_UPDATE_FIXTURES=1 pytest.
    """
    import os

    dest = Path(__file__).resolve().parents[2] / "site" / "src" / "lib" / "__fixtures__"
    if not dest.is_dir():
        import pytest

        pytest.skip("站点目录不在此 checkout 中")

    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    pairs = [
        (data / "index.json", dest / "index.fixture.json"),
        (data / "details" / "mini.json", dest / "detail.fixture.json"),
    ]
    if os.environ.get("OPF_UPDATE_FIXTURES"):
        for src, dst in pairs:
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return
    for src, dst in pairs:
        fresh = json.loads(src.read_text(encoding="utf-8"))
        fresh.pop("generatedAt", None)
        committed = json.loads(dst.read_text(encoding="utf-8"))
        committed.pop("generatedAt", None)
        assert fresh == committed, (
            f"{dst.name} 已过期，跑 OPF_UPDATE_FIXTURES=1 pytest 更新"
        )


def test_family_scripts_drop_partial_when_a_variant_is_complete():
    """If any one size in a family is fully covered, the family should not still carry a "(partial)" tag.

    A family's scripts are the union of its variants'. For fonts like Ark Pixel, where
    small sizes have incomplete coverage but large sizes are fully covered, the union
    would otherwise contain both zh-hans and zh-hans-partial.
    """
    from opf.build import merge_scripts

    assert merge_scripts(
        ["zh-hans-partial", "ja-partial", "latin", "zh-hans"]
    ) == ["ja-partial", "latin", "zh-hans"]
    # A "partial" tag with no matching complete entry should be kept
    assert merge_scripts(["ja-partial", "latin"]) == ["ja-partial", "latin"]


def test_family_toml_top_level_keys_are_before_any_table():
    """Top-level keys must be written before the first [table header].

    When appending `exclude = [...]` to the end of family.toml, if the file already
    has a [license] section, the key silently lands inside the license table instead
    of the top level -- TOML still parses fine, it's just unreadable from where it's expected.
    """
    import tomllib
    from pathlib import Path

    root = Path(__file__).resolve().parents[2] / "fonts"
    if not root.is_dir():
        import pytest

        pytest.skip("字体目录不在此 checkout 中")
    top_level = {"merge_subsets", "merge", "exclude", "sample_lang", "added",
                 "form", "vibes", "curated"}
    bad = []
    for toml_path in sorted(root.glob("*/family.toml")):
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
        for table in ("license", "samples", "variants"):
            stray = top_level & set(data.get(table) or {})
            if stray:
                bad.append(f"{toml_path.parent.name}: {sorted(stray)} 落进了 [{table}]")
    assert not bad, "\n".join(bad)


def test_search_text_is_recomputed_on_cache_hit(tmp_path):
    """searchText is a pure function of the metadata, so it must not go stale along with the cache.

    The cache key only tracks font files, family.toml, and the pipeline version --
    changing variants.py's expansion rules doesn't invalidate it. If searchText were
    stored in the cache, a rule change wouldn't show up until a full rebuild (131
    families takes half an hour). So it's recomputed on every cache hit instead.
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)

    # Corrupt the cached searchText to simulate "expansion rules changed, cache is stale"
    cached = cache / "families" / "mini.json"
    payload = json.loads(cached.read_text(encoding="utf-8"))
    payload["index_entry"]["searchText"] = "STALE"
    cached.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = build(fonts, data, dl, cache)
    assert report.cached == 2, "第二遍应当全部命中缓存"

    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    mini = next(f for f in idx["families"] if f["slug"] == "mini")
    assert mini["searchText"] != "STALE"
    assert "MiniOld" in mini["searchText"]


def _retoml(fonts, **edits):
    """Edit mini's family.toml, returning the text before the change."""
    f = fonts / "mini" / "family.toml"
    before = f.read_text(encoding="utf-8")
    text = before
    for key, line in edits.items():
        text = "\n".join(
            line if l.startswith(key + " = ") else l for l in text.split("\n")
        )
    f.write_text(text, encoding="utf-8")
    return before


def test_descriptive_edit_skips_the_expensive_rebuild(tmp_path):
    """Editing only display fields should not recompute glyphs -- but all text in the output must still refresh.

    Re-vectorizing 131 families over an author-name change would take half an hour,
    and an author name changes no glyph outlines. So the cache key only tracks font
    files and family.toml's structural fields.
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    packs = data / "packs" / "mini"
    before_mtimes = {p: p.stat().st_mtime_ns for p in packs.rglob("*") if p.is_file()}

    _retoml(fonts, authors='authors = ["新作者 (handle)"]',
            description='description = "改过的简介"')
    report = build(fonts, data, dl, cache)

    assert report.cached == 2, "只改展示字段不该触发重建"
    # Not a single byte of the glyph output should change
    assert {p: p.stat().st_mtime_ns for p in packs.rglob("*") if p.is_file()} \
        == before_mtimes

    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    mini = next(f for f in idx["families"] if f["slug"] == "mini")
    assert mini["authors"] == ["新作者 (handle)"]
    assert "新作者" in mini["searchText"]

    detail = json.loads((data / "details" / "mini.json").read_text(encoding="utf-8"))
    assert detail["description"] == "改过的简介"
    assert detail["meta"]["authors"] == ["新作者 (handle)"]


def test_descriptive_edit_gives_the_same_bytes_as_a_full_rebuild(tmp_path):
    """The fast path and a full rebuild must produce identical downloads -- the sha256 gets published."""
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    _retoml(fonts, authors='authors = ["新作者 (handle)"]')
    build(fonts, data, dl, cache)                      # fast path
    fast = json.loads((data / "details" / "mini.json").read_text(encoding="utf-8"))

    # control group: same fonts directory, empty cache, empty output, full rebuild
    fonts2, data2, dl2, cache2 = _setup(tmp_path / "again")
    shutil.copy(fonts / "mini" / "family.toml", fonts2 / "mini" / "family.toml")
    build(fonts2, data2, dl2, cache2)
    full = json.loads((data2 / "details" / "mini.json").read_text(encoding="utf-8"))

    assert fast["downloads"] == full["downloads"]
    assert fast["meta"] == full["meta"]


def test_structural_edit_still_forces_a_rebuild(tmp_path):
    # Renaming the font gets written into the TTF and the OG image, so it must still trigger a rebuild
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    _retoml(fonts, name='name = "Renamed"')
    report = build(fonts, data, dl, cache)
    assert report.cached == 1, "改 name 属于结构性变更，mini 应当重建"


def test_parallel_and_serial_builds_agree(tmp_path, monkeypatch):
    """Parallelism is only a scheduling mechanism -- output must be byte-identical to the serial build."""
    fonts1, data1, dl1, cache1 = _setup(tmp_path / "par")
    build(fonts1, data1, dl1, cache1)          # 默认并行

    monkeypatch.setenv("OPF_JOBS", "1")
    fonts2, data2, dl2, cache2 = _setup(tmp_path / "ser")
    build(fonts2, data2, dl2, cache2)

    assert (data1 / "index.json").read_bytes() == (data2 / "index.json").read_bytes()
    assert (dl1 / "manifest.json").read_bytes() == (dl2 / "manifest.json").read_bytes()
    for p1 in sorted(data1.rglob("*")):
        if not p1.is_file():
            continue
        p2 = data2 / p1.relative_to(data1)
        assert p2.exists() and p1.read_bytes() == p2.read_bytes(), p1.name


def test_index_carries_per_variant_ink_heights(tmp_path):
    """Ink height must be reported per-variant, not just the family max.

    WenQuanYi Bitmap Song's five variants have ink heights 11/12/13/14/16; reporting
    only max=16 would make it unsearchable when filtering by 14-14 -- even though it
    does have a 14 variant.
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    mini = next(f for f in idx["families"] if f["slug"] == "mini")
    assert mini["inkHeights"] == sorted(set(mini["inkHeights"]))
    assert mini["inkHeights"], "每个家族至少有一个变体的墨迹高度"
    assert max(mini["inkHeights"]) == mini["inkHeight"]  # the legacy field still holds the max


def test_family_only_build_keeps_other_families_outputs(tmp_path):
    """--family should only rebuild the given family, and must never delete other families' output.

    When the entire cache is invalidated (e.g. right after bumping PIPELINE_VERSION),
    none of the other families hit cache. The old implementation would drop them from
    entries, and _prune_orphans would then delete all of them as orphans.
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    others = sorted(p.name for p in (data / "details").glob("*.json"))
    assert len(others) > 1

    import shutil
    shutil.rmtree(cache)                      # simulate the whole cache being invalidated
    build(fonts, data, dl, cache, only_family="mini")

    still = sorted(p.name for p in (data / "details").glob("*.json"))
    assert still == others, f"其他家族的产物被删了：{set(others) - set(still)}"


def test_zero_glyph_variant_fails_the_family(tmp_path):
    """When an unresolved charset leaves zero glyphs, the whole family must fail the build rather than publish an empty font."""
    fonts = tmp_path / "fonts"
    fam = fonts / "ghost"
    fam.mkdir(parents=True)
    # A proprietary encoding like Adobe FontSpecific can't be mapped by decode_cp, so all glyphs get dropped
    (fam / "ghost.bdf").write_text(
        "STARTFONT 2.1\n"
        "FONT -Adobe-Symbol-Medium-R-Normal--12-120-100-100-P-95-Adobe-FontSpecific\n"
        "SIZE 12 100 100\nFONTBOUNDINGBOX 8 12 0 -2\n"
        'STARTPROPERTIES 3\nCHARSET_REGISTRY "Adobe"\n'
        'CHARSET_ENCODING "FontSpecific"\nPIXEL_SIZE 12\nENDPROPERTIES\n'
        "CHARS 1\nSTARTCHAR alpha\nENCODING 97\nSWIDTH 500 0\nDWIDTH 6 0\n"
        "BBX 4 4 0 0\nBITMAP\n60\n90\n90\n60\nENDCHAR\nENDFONT\n",
        encoding="utf-8",
    )
    (fam / "family.toml").write_text('name = "Ghost"\nform = "other"\n', encoding="utf-8")
    report = build(fonts, tmp_path / "data", tmp_path / "dl", tmp_path / "cache")
    assert any("ghost" in w and "构建失败" in w for w in report.warnings), report.warnings
    assert not (tmp_path / "data" / "details" / "ghost.json").exists()
