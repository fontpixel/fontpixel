"""附加产物:查字覆盖区间表与字表元数据 JSON。"""

from __future__ import annotations

import gzip
import json
import struct
from pathlib import Path

from fbf.coverage.charsets import SECTION_ORDER, Charset


def cps_to_runs(cps: frozenset[int] | set[int]) -> list[tuple[int, int]]:
    """码位集合 → 合并后的半开区间 [(start, end), ...]。"""
    runs: list[tuple[int, int]] = []
    for cp in sorted(cps):
        if runs and cp == runs[-1][1]:
            runs[-1] = (runs[-1][0], cp + 1)
        else:
            runs.append((cp, cp + 1))
    return runs


def write_intervals(runs_by_slug: dict[str, list[tuple[int, int]]], out: Path) -> None:
    buf = bytearray()
    buf += struct.pack("<I", len(runs_by_slug))
    for slug in sorted(runs_by_slug):
        raw = slug.encode("utf-8")
        buf += struct.pack("<H", len(raw))
        buf += raw
        runs = runs_by_slug[slug]
        buf += struct.pack("<I", len(runs))
        for a, b in runs:
            buf += struct.pack("<II", a, b)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(gzip.compress(bytes(buf), compresslevel=9, mtime=0))


def read_intervals(path: Path) -> dict[str, list[tuple[int, int]]]:
    raw = gzip.decompress(path.read_bytes())
    pos = 0
    (count,) = struct.unpack_from("<I", raw, pos)
    pos += 4
    out: dict[str, list[tuple[int, int]]] = {}
    for _ in range(count):
        (slen,) = struct.unpack_from("<H", raw, pos)
        pos += 2
        slug = raw[pos : pos + slen].decode("utf-8")
        pos += slen
        (n,) = struct.unpack_from("<I", raw, pos)
        pos += 4
        runs = []
        for _ in range(n):
            a, b = struct.unpack_from("<II", raw, pos)
            pos += 8
            runs.append((a, b))
        out[slug] = runs
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
