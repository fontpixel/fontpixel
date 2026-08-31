"""Facts cache: entries store raw facts (file hashes + toml snapshot); a cache hit
applies the current structural-field policy at comparison time. This means changing
the policy itself (adding/removing _STRUCTURAL_KEYS) no longer invalidates the whole
cache -- the 52-minute full rebuild on 2026-08-30 was caused by exactly this: changing
the key algorithm and forgetting to migrate.
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
    """Core guarantee: changing only the "which fields count as structural" policy,
    with no value change, must not trigger a rebuild.

    The policy lives in code and is applied to the stored snapshot and the current
    file only at comparison time; both sides take their subset using the same policy,
    so the policy itself is never a reason for a cache miss.
    """
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    monkeypatch.setattr(cache, "_STRUCTURAL_KEYS",
                        cache._STRUCTURAL_KEYS + ("vibes",))
    assert facts_match(stored, family_facts("dh", d))
    # Once a newly-included field's value actually changes, it should rebuild
    (d / "family.toml").write_text(TOML.replace('["retro-game"]', '["cute"]'),
                                   encoding="utf-8")
    assert not facts_match(stored, family_facts("dh", d))


def test_unparseable_toml_never_matches_a_parsed_snapshot(tmp_path):
    d = _dir(tmp_path)
    stored = family_facts("dh", d)
    (d / "family.toml").write_text('name = "Fam', encoding="utf-8")  # missing closing quote
    broken = family_facts("dh", d)
    assert not facts_match(stored, broken)
    # A broken file matches itself: no rebuilding the same broken state every time
    assert facts_match(broken, family_facts("dh", d))


def test_facts_survive_json_roundtrip(tmp_path):
    # Cache entries must survive json.dumps; non-JSON scalars like dates are normalized to strings
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
