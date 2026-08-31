"""Internal font model (contract C3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Glyph:
    cp: int
    name: str
    dwidth: int
    bbw: int
    bbh: int
    bbx: int
    bby: int
    rows: bytes  # bbh * ceil(bbw/8) bytes, rows top to bottom, bits MSB-first


@dataclass
class ParsedFont:
    path: Path
    family_slug: str
    file_name: str
    props: dict[str, str | int]
    pixel_size: int
    ascent: int
    descent: int
    bbox: tuple[int, int, int, int]  # (w, h, xoff, yoff)
    glyphs: list[Glyph] = field(default_factory=list)  # ascending by cp, ENCODING>=0 only
    warnings: list[str] = field(default_factory=list)


def row_bytes(bbw: int) -> int:
    return (bbw + 7) // 8
