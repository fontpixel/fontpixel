"""内部字体模型(契约 C3)。"""

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
    rows: bytes  # bbh * ceil(bbw/8) 字节,行序自上而下,位 MSB-first


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
    glyphs: list[Glyph] = field(default_factory=list)  # cp 升序,仅 ENCODING>=0
    warnings: list[str] = field(default_factory=list)


def row_bytes(bbw: int) -> int:
    return (bbw + 7) // 8
