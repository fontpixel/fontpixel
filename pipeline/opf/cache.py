"""Family-level incremental cache: entries store "facts", and policy is applied to them at comparison time to decide a hit.

Facts = charset data hash (including the pipeline version) + a hash of
every file in the family directory + a full parsed snapshot of
family.toml. Policy = which toml fields count as "structural"
(_STRUCTURAL_KEYS), which lives only in code and gets applied to both the
stored snapshot and the current files only when facts_match compares them.

Why not store a precomputed key instead: whenever the key algorithm
changes (even just adjusting the list of structural fields), every opaque
hash stops matching, and the only fix is remembering to run a migration
script — on 2026-08-30 forgetting to do that cost a 52-minute full
rebuild. Storing facts avoids this failure mode: when policy changes, both
sides take the subset under the new policy, and unchanged values still hit.
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import opf


def data_dir_hash(data_dir: Path) -> str:
    h = hashlib.sha256()
    h.update(f"pipeline:{opf.PIPELINE_VERSION}".encode())
    for p in sorted(data_dir.rglob("*.txt")):
        h.update(p.relative_to(data_dir).as_posix().encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


# The family.toml keys that change "what gets built." Everything else is
# purely display text, and changing it doesn't require recomputing glyph
# packs, coverage, or TTF outlines — see build.py's fast path.
#
#   merge / merge_subsets / exclude  which glyphs get built
#   variants                         variant id, size, weight, layout
#   license                          license output and the TTF copyright line
#   converted_from                   the "converted from" marker
#   name                             baked into the OG image (only this one — per-language names never enter build output)
#   samples / sample_lang            picking sample text depends on the
#                                    font's actual coverage, which isn't
#                                    known without a parsed font
_STRUCTURAL_KEYS = (
    "merge", "merge_subsets", "exclude", "variants", "license",
    "converted_from", "name", "samples", "sample_lang",
)


def family_facts(data_hash: str, family_dir: Path) -> dict:
    """Gather all current facts for a family, to be stored as part of its cache entry.

    family.toml is stored as a parsed snapshot rather than a hash — a hit
    check needs to pull the structural subset from it "as policy stood at
    comparison time." When it can't be parsed (a corrupt file), store a
    whole-file hash instead, so it neither false-hits nor rebuilds the
    same broken state every single time.
    """
    files: dict[str, str] = {}
    toml_snapshot: dict | None = None
    for p in sorted(family_dir.iterdir()):
        if not p.is_file():
            continue
        if p.name == "family.toml":
            try:
                raw = tomllib.loads(p.read_text(encoding="utf-8"))
                # Round-trip through JSON: non-JSON scalars like dates get
                # normalized to strings, so "facts computed now" and
                # "facts read back from a cache entry" are byte-for-byte comparable.
                toml_snapshot = json.loads(
                    json.dumps(raw, ensure_ascii=False, sort_keys=True,
                               default=str))
            except (OSError, tomllib.TOMLDecodeError):
                toml_snapshot = {
                    "__unparseable__":
                        hashlib.sha256(p.read_bytes()).hexdigest()
                }
            continue
        files[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"data_hash": data_hash, "files": files, "toml": toml_snapshot}


def structural_subset(toml_snapshot: dict | None) -> str:
    """Extract the structural subset of a toml snapshot under current policy, normalized into a comparable string."""
    if not isinstance(toml_snapshot, dict):
        return "__missing__"
    subset = {k: toml_snapshot[k] for k in _STRUCTURAL_KEYS
              if k in toml_snapshot}
    if "__unparseable__" in toml_snapshot:
        subset["__unparseable__"] = toml_snapshot["__unparseable__"]
    return json.dumps(subset, sort_keys=True, ensure_ascii=False, default=str)


def facts_match(stored: dict | None, current: dict) -> bool:
    """Whether stored facts and current facts are equivalent (equivalent ⇒ glyph output can be reused).

    Files are compared hash by hash; family.toml is compared only on its
    structural subset — display-field changes get backfilled by build.py's
    fast path instead of triggering a rebuild.
    """
    if not isinstance(stored, dict):
        return False
    return (
        stored.get("data_hash") == current["data_hash"]
        and stored.get("files") == current["files"]
        and structural_subset(stored.get("toml"))
            == structural_subset(current["toml"])
    )


class FamilyCache:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir / "families"
        self.dir.mkdir(parents=True, exist_ok=True)

    def load(self, slug: str, facts: dict) -> dict | None:
        p = self.dir / f"{slug}.json"
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not facts_match(data.get("facts"), facts):
            return None
        return data

    def store(self, slug: str, payload: dict) -> None:
        (self.dir / f"{slug}.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
