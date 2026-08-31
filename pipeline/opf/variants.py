"""Simplified/Traditional and variant-character normalization: makes searching "东云" match "東雲" and vice versa.

Data comes from Unicode Unihan's kSimplifiedVariant / kTraditionalVariant,
merged into equivalence classes (see textdata/st-variants.txt). Expansion
happens at build time — the index stores every spelling directly, so the
frontend never has to load a mapping table.
"""

from __future__ import annotations

import functools
from pathlib import Path

DATA = Path(__file__).parent / "textdata" / "st-variants.txt"


@functools.cache
def variant_map(path: Path = DATA) -> dict[str, str]:
    """Character → every spelling in its equivalence class (itself included)."""
    table: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for ch in line:
            table[ch] = line
    return table


# Cap on how many spellings one field expands into. Real font names have
# few variant characters, so this is plenty; if a string happens to have
# an unusually large number of them, only the earliest positions get
# expanded, keeping the combination count from running away.
_MAX_RENDERINGS = 64


def expand(text: str) -> str:
    """Expand text into "original + every Simplified/Traditional/variant spelling," for search matching.

    Can't just index the i-th member of each equivalence class —
    textdata/st-variants.txt doesn't keep a consistent member order across
    groups (Traditional comes first in "驛驿", Simplified comes first in
    "点點"), so doing that would only produce a mixed-up string like
    "文泉驛点阵宋体," and neither the all-Traditional nor the all-Simplified
    spelling would be searchable. So instead, take the Cartesian product
    character by character, listing out every spelling of the string.
    """
    if not text:
        return ""
    table = variant_map()
    outs = [""]
    for ch in text:
        group = table.get(ch)
        # Once the combination count exceeds the cap, keep remaining characters as-is — at least don't lose the original spelling.
        if not group or len(outs) * len(group) > _MAX_RENDERINGS:
            outs = [o + ch for o in outs]
        else:
            outs = [o + c for o in outs for c in group]
    seen = dict.fromkeys([text, *outs])
    return " ".join(seen)


def search_text(*fields: str) -> str:
    """Join several fields into one searchable text, with Simplified/Traditional expansion applied."""
    seen: list[str] = []
    for f in fields:
        if f and f not in seen:
            seen.append(f)
    # Expand field by field: doing the Cartesian product across the whole joined string would blow up the combination count once there are enough variant characters.
    return " ".join(expand(f) for f in seen)
