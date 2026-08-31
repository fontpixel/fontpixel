"""事实缓存:条目存原始事实(文件哈希 + toml 快照),命中判定在比对时套用
当前的结构性字段政策。这样改政策本身(增删 _STRUCTURAL_KEYS)不再让全部
缓存失效——2026-08-30 那次 52 分钟全量重建就是「改了键算法忘了迁移」造成的。
"""

import json
from pathlib import Path

import pytest

import opf.cache as cache
from opf.cache import FamilyCache, facts_match, family_facts, structural_subset

TOML = """\
name = "Fam"
authors = ["Alice"]
description = "一句话"
vibes = ["retro-game"]

[license]
spdx = "OFL-1.1"
"""


def _dir(tmp_path: Path, toml: str = TOML, font: bytes = b"STARTFONT") -> Path:
    d = tmp_path / "fam"
    d.mkdir(exist_ok=True)
    (d / "family.toml").write_text(toml, encoding="utf-8")
    (d / "fam.bdf").write_bytes(font)
    return d


def test_descriptive_toml_edit_still_matches(tmp_path):
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    (d / "family.toml").write_text(
        TOML.replace('authors = ["Alice"]', 'authors = ["Bob"]')
            .replace('description = "一句话"', 'description = "另一句"'),
        encoding="utf-8")
    assert facts_match(stored, family_facts("dh", d))


def test_structural_toml_edit_mismatches(tmp_path):
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    (d / "family.toml").write_text(TOML.replace('name = "Fam"', 'name = "Ren"'),
                                   encoding="utf-8")
    assert not facts_match(stored, family_facts("dh", d))


def test_font_file_change_mismatches(tmp_path):
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    (d / "fam.bdf").write_bytes(b"STARTFONT 2.1")
    assert not facts_match(stored, family_facts("dh", d))


def test_data_hash_change_mismatches(tmp_path):
    d = _dir(tmp_path)
    assert not facts_match(family_facts("dh", d), family_facts("dh2", d))


def test_policy_change_alone_keeps_the_hit(tmp_path, monkeypatch):
    """核心保证：只改「哪些字段算结构性」这个政策，值没变就不重建。

    政策活在代码里，比对时才套用到存档快照与当前文件上；两边用同一份
    政策取子集，所以政策本身不构成失效理由。
    """
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    monkeypatch.setattr(cache, "_STRUCTURAL_KEYS",
                        cache._STRUCTURAL_KEYS + ("vibes",))
    assert facts_match(stored, family_facts("dh", d))
    # 新纳入的字段一旦取值真的变了，就该重建
    (d / "family.toml").write_text(TOML.replace('["retro-game"]', '["cute"]'),
                                   encoding="utf-8")
    assert not facts_match(stored, family_facts("dh", d))


def test_unparseable_toml_never_matches_a_parsed_snapshot(tmp_path):
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    (d / "family.toml").write_text('name = "Fam', encoding="utf-8")  # 缺引号
    broken = family_facts("dh", d)
    assert not facts_match(stored, broken)
    # 坏文件与自身一致：不至于每次都重建同一个坏状态
    assert facts_match(broken, family_facts("dh", d))


def test_facts_survive_json_roundtrip(tmp_path):
    # 缓存条目要过 json.dumps；日期等非 JSON 标量按字符串归一
    d = _dir(tmp_path, TOML + 'added = 2026-08-30\n')
    facts = family_facts("dh", d)
    thawed = json.loads(json.dumps(facts, ensure_ascii=False, sort_keys=True))
    assert facts_match(thawed, family_facts("dh", d))


def test_cache_load_requires_facts(tmp_path):
    c = FamilyCache(tmp_path)
    (c.dir / "fam.json").write_text(
        json.dumps({"key": "legacy-opaque-hash", "index_entry": {}}),
        encoding="utf-8")
    assert c.load("fam", family_facts("dh", _dir(tmp_path))) is None


def test_cache_roundtrip(tmp_path):
    d = _dir(tmp_path)
    c = FamilyCache(tmp_path)
    facts = family_facts("dh", d)
    c.store("fam", {"facts": facts, "index_entry": {"slug": "fam"}})
    got = c.load("fam", family_facts("dh", d))
    assert got is not None and got["index_entry"]["slug"] == "fam"
    assert c.load("fam", family_facts("other", d)) is None
