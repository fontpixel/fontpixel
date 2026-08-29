"""Unicode 区段与已指派码位(数据由 gen_tables.py 生成并入库)。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_BLOCK_RE = re.compile(r"^([0-9A-F]+)\.\.([0-9A-F]+);\s*(.+)$")
_RANGE_RE = re.compile(r"^([0-9A-F]+)\.\.([0-9A-F]+)$")


@dataclass
class Ucd:
    blocks: list[tuple[str, int, int]]
    assigned: frozenset[int]
    block_assigned_counts: dict[str, int]


def load_ucd(ucd_dir: Path) -> Ucd:
    blocks: list[tuple[str, int, int]] = []
    for line in (ucd_dir / "Blocks.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _BLOCK_RE.match(line)
        if m:
            blocks.append((m.group(3).strip(), int(m.group(1), 16), int(m.group(2), 16)))

    assigned: set[int] = set()
    for line in (ucd_dir / "assigned-ranges.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = _RANGE_RE.match(line)
        if m:
            assigned.update(range(int(m.group(1), 16), int(m.group(2), 16) + 1))

    frozen = frozenset(assigned)
    counts: dict[str, int] = {}
    for name, start, end in blocks:
        counts[name] = sum(1 for cp in range(start, end + 1) if cp in frozen)
    return Ucd(blocks=blocks, assigned=frozen, block_assigned_counts=counts)
