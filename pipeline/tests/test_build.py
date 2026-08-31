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

    # 曾用名／别名进搜索文本，中文别名和家族名一样做简繁展开
    assert "MiniOld" in mini["searchText"]
    assert "迷你旧名" in mini["searchText"]
    assert "舊" in mini["searchText"]
    # 并列作者原样下发，前端逐个做成按作者名搜索的链接
    assert mini["authors"] == ["PFC Tests", "Second Author"]
    assert mini["authorsEn"] == ["PFC Tests", "Second Author"]

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
    # hiragana 共 86 字,mini 全缺(≤500)→ 提供缺字列表
    assert len(detail["missingChars"][vid]["hiragana"]) == 86
    # gb2312 缺 6763 个(>500)→ 不提供
    assert "gb2312" not in detail["missingChars"][vid]

    charsets = json.loads((data / "charsets.json").read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in charsets["charsets"]}
    assert by_id["gb2312"]["nameZh"].startswith("GB/T 2312")
    assert by_id["gb2312"]["total"] == 6763
    assert by_id["gb2312"]["section"] == "gb"
    assert charsets["sections"][0] == "gb"

    # 缓存后重跑,intervals 仍完整(来自缓存 payload)
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

    # 修改结构性字段 → 只重建该家族（各语言名是描述性的，走快路径，另有测试）
    toml = fonts / "mini" / "family.toml"
    toml.write_text(toml.read_text().replace('name = "Mini Test"', 'name = "Mini Test 2"'),
                    encoding="utf-8")
    report3 = build(fonts, data, dl, cache)
    assert report3.cached == 1
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert {f["slug"]: f for f in idx["families"]}["mini"]["name"] == "Mini Test 2"


def test_broken_family_isolated(tmp_path):
    """单个家族的 family.toml 损坏不应拖垮整个构建。"""
    fonts, data, dl, cache = _setup(tmp_path)
    (fonts / "mini" / "family.toml").write_text("这不是合法的 TOML ===", encoding="utf-8")
    report = build(fonts, data, dl, cache)
    assert report.failed == 1
    assert any("mini" in w and "失败" in w for w in report.warnings)
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert [f["slug"] for f in idx["families"]] == ["nometa"]  # 其余家族照常


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
    # mini.bdf 与 mini.bdf.gz 同名 → id 冲突,应加后缀并告警
    shutil.copy(FIX / "fonts-tree" / "mini" / "mini2.bdf.gz",
                fonts / "mini" / "mini.bdf.gz")
    report = build(fonts, data, dl, cache, only_family="mini")
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    ids = [v["id"] for f in idx["families"] for v in f["variants"]]
    assert len(ids) == len(set(ids))
    assert any("collision" in w or "冲突" in w for w in report.warnings)


def test_ts_fixtures_in_sync(tmp_path):
    """站点的 zod 契约夹具必须跟管线的真实产物一致。

    夹具原本靠手工拷贝，改了 index/detail 的结构就会悄悄过期，vitest 那边
    才报错。这里直接拿构建产物比对；要更新就跑 OPF_UPDATE_FIXTURES=1 pytest。
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
    """家族里只要有一个尺寸达标，就不该再同时挂着「（不完整）」标签。

    家族的 scripts 是各变体的并集，方舟像素这类字体的小尺寸覆盖不全、
    大尺寸达标，并集里会同时出现 zh-hans 和 zh-hans-partial。
    """
    from opf.build import merge_scripts

    assert merge_scripts(
        ["zh-hans-partial", "ja-partial", "latin", "zh-hans"]
    ) == ["ja-partial", "latin", "zh-hans"]
    # 没有对应完整档的「不完整」标签要保留
    assert merge_scripts(["ja-partial", "latin"]) == ["ja-partial", "latin"]


def test_family_toml_top_level_keys_are_before_any_table():
    """顶层键必须写在第一个 [表头] 之前。

    往 family.toml 末尾追加 `exclude = [...]` 时，如果文件已有 [license] 段，
    这个键会静默落进 license 表里而不是顶层——TOML 照样解析成功，只是读不到。
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
    """searchText 是元数据的纯函数，不该跟着缓存一起变陈旧。

    缓存键只认字体文件、family.toml 与管线版本，改 variants.py 的展开
    规则不会让它失效——若 searchText 存在缓存里，规则改了也刷不出来，
    除非全量重建一次（131 个家族要半小时）。所以命中缓存时现算。
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)

    # 把缓存里的 searchText 改坏，模拟「展开规则变了、缓存还是旧的」
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
    """改 mini 的 family.toml，返回改动前的原文。"""
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
    """只改展示字段时，不该重算字形——但产物里的文本必须全部刷新。

    改一个作者名就把 131 个家族重新矢量化要半小时，而作者名并不改变任何
    字形轮廓。缓存键因此只认字体文件与 family.toml 的结构性字段。
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    packs = data / "packs" / "mini"
    before_mtimes = {p: p.stat().st_mtime_ns for p in packs.rglob("*") if p.is_file()}

    _retoml(fonts, authors='authors = ["新作者 (handle)"]',
            description='description = "改过的简介"')
    report = build(fonts, data, dl, cache)

    assert report.cached == 2, "只改展示字段不该触发重建"
    # 字形产物一个字节都不该动
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
    """快路径与全量重建必须产出同样的下载物——sha256 是要发布出去的。"""
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    _retoml(fonts, authors='authors = ["新作者 (handle)"]')
    build(fonts, data, dl, cache)                      # 快路径
    fast = json.loads((data / "details" / "mini.json").read_text(encoding="utf-8"))

    # 参照组：同样的 fonts 目录，空缓存、空产物，整个重来一遍
    fonts2, data2, dl2, cache2 = _setup(tmp_path / "again")
    shutil.copy(fonts / "mini" / "family.toml", fonts2 / "mini" / "family.toml")
    build(fonts2, data2, dl2, cache2)
    full = json.loads((data2 / "details" / "mini.json").read_text(encoding="utf-8"))

    assert fast["downloads"] == full["downloads"]
    assert fast["meta"] == full["meta"]


def test_structural_edit_still_forces_a_rebuild(tmp_path):
    # 改字体名会写进 TTF 与 OG 图，必须照常重建
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    _retoml(fonts, name='name = "Renamed"')
    report = build(fonts, data, dl, cache)
    assert report.cached == 1, "改 name 属于结构性变更，mini 应当重建"


def test_parallel_and_serial_builds_agree(tmp_path, monkeypatch):
    """并行只是调度方式，产物必须与串行逐字节一致。"""
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
    """墨迹高度要逐变体下发，不能只给家族最大值。

    文泉驿点阵宋体的五个变体墨迹高是 11/12/13/14/16，只下发 max=16 的话，
    按 14-14 筛选就搜不到它——而它确实有一个 14 的变体。
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    idx = json.loads((data / "index.json").read_text(encoding="utf-8"))
    mini = next(f for f in idx["families"] if f["slug"] == "mini")
    assert mini["inkHeights"] == sorted(set(mini["inkHeights"]))
    assert mini["inkHeights"], "每个家族至少有一个变体的墨迹高度"
    assert max(mini["inkHeights"]) == mini["inkHeight"]  # 旧字段仍是最大值


def test_family_only_build_keeps_other_families_outputs(tmp_path):
    """--family 只该重建指定家族，绝不能删掉别人的产物。

    缓存整体失效时（例如刚升过 PIPELINE_VERSION），其余家族一个都命中不了，
    旧实现会把它们从 entries 里漏掉，然后 _prune_orphans 当作孤儿全删。
    """
    fonts, data, dl, cache = _setup(tmp_path)
    build(fonts, data, dl, cache)
    others = sorted(p.name for p in (data / "details").glob("*.json"))
    assert len(others) > 1

    import shutil
    shutil.rmtree(cache)                      # 模拟缓存整体失效
    build(fonts, data, dl, cache, only_family="mini")

    still = sorted(p.name for p in (data / "details").glob("*.json"))
    assert still == others, f"其他家族的产物被删了：{set(others) - set(still)}"


def test_zero_glyph_variant_fails_the_family(tmp_path):
    """字符集没解开导致零字形时，整族必须构建失败，不能发布空字体。"""
    fonts = tmp_path / "fonts"
    fam = fonts / "ghost"
    fam.mkdir(parents=True)
    # Adobe FontSpecific 这类自有编码，decode_cp 无法映射，字形会被全部丢弃
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
