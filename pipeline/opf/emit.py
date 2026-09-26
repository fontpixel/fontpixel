"""Auxiliary output: the coverage interval lookup table and charset metadata JSON."""

from __future__ import annotations

import gzip
import json
import struct
from pathlib import Path

from opf.coverage.charsets import SECTION_ORDER, Charset


def cps_to_runs(cps: frozenset[int] | set[int]) -> list[tuple[int, int]]:
    """Codepoint set → merged half-open intervals [(start, end), ...]."""
    runs: list[tuple[int, int]] = []
    for cp in sorted(cps):
        if runs and cp == runs[-1][1]:
            runs[-1] = (runs[-1][0], cp + 1)
        else:
            runs.append((cp, cp + 1))
    return runs


def write_intervals(runs_by_slug: dict[str, dict[str, list[tuple[int, int]]]], out: Path) -> None:
    """Per-variant code point runs (see site/src/lib/intervals.ts for the reader).

    Layout inside gzip, little-endian: u32 familyCount; per family: u16 slugLen
    + utf8 slug, u16 setCount, setCount × (u32 runCount, runCount × (u32 start,
    u32 end)), u16 variantCount, variantCount × (u16 idLen + utf8 id, u16 set).
    Variants with identical coverage (bold, oblique, subsets) share one set.
    """
    buf = bytearray()
    buf += struct.pack("<I", len(runs_by_slug))
    for slug in sorted(runs_by_slug):
        raw = slug.encode("utf-8")
        buf += struct.pack("<H", len(raw))
        buf += raw
        sets: list[tuple[tuple[int, int], ...]] = []
        index_of: dict[tuple[tuple[int, int], ...], int] = {}
        variant_sets: list[tuple[str, int]] = []
        for vid, runs in runs_by_slug[slug].items():
            key = tuple(tuple(r) for r in runs)
            if key not in index_of:
                index_of[key] = len(sets)
                sets.append(key)
            variant_sets.append((vid, index_of[key]))
        buf += struct.pack("<H", len(sets))
        for runs in sets:
            buf += struct.pack("<I", len(runs))
            for a, b in runs:
                buf += struct.pack("<II", a, b)
        buf += struct.pack("<H", len(variant_sets))
        for vid, index in variant_sets:
            raw = vid.encode("utf-8")
            buf += struct.pack("<H", len(raw)) + raw + struct.pack("<H", index)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(gzip.compress(bytes(buf), compresslevel=9, mtime=0))


def read_intervals(path: Path) -> dict[str, dict[str, list[tuple[int, int]]]]:
    raw = gzip.decompress(path.read_bytes())
    pos = 0

    def take(fmt: str):
        nonlocal pos
        values = struct.unpack_from(fmt, raw, pos)
        pos += struct.calcsize(fmt)
        return values

    def text() -> str:
        nonlocal pos
        (n,) = take("<H")
        pos += n
        return raw[pos - n : pos].decode("utf-8")

    out: dict[str, dict[str, list[tuple[int, int]]]] = {}
    (count,) = take("<I")
    for _ in range(count):
        slug = text()
        (n_sets,) = take("<H")
        sets = []
        for _ in range(n_sets):
            (n,) = take("<I")
            sets.append([take("<II") for _ in range(n)])
        (n_variants,) = take("<H")
        out[slug] = {}
        for _ in range(n_variants):
            vid = text()
            (index,) = take("<H")
            out[slug][vid] = sets[index]
    return out


def write_charsets_json(charsets: list[Charset], out: Path) -> None:
    data = {
        "sections": SECTION_ORDER,
        "charsets": [
            {
                "id": c.id,
                "section": c.section,
                "order": c.order,
                "nameZh": c.name_zh,
                "nameEn": c.name_en,
                "descZh": c.desc_zh,
                "descEn": c.desc_en,
                "source": c.source,
                "total": len(c.cps),
            }
            for c in charsets
        ],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
