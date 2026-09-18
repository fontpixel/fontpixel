"""Convert t-mat and dhepper's C bitmap tables without rasterizing their pixels."""
from __future__ import annotations

import re
from pathlib import Path

from opf.model import Glyph, ParsedFont

_REVERSE = bytes(int(f"{n:08b}"[::-1], 2) for n in range(256))


def _font(path: Path, slug: str, rows: dict[int, bytes], copyright: str,
          warnings: list[str] | None = None) -> ParsedFont:
    if not rows:
        raise ValueError(f"{path}: no encoded 8x8 glyphs")
    return ParsedFont(
        path=path, family_slug=slug, file_name=f"{slug}-8px.bdf",
        props={"COPYRIGHT": copyright, "CHARSET_REGISTRY": "ISO10646",
               "CHARSET_ENCODING": "1", "SPACING": "C"},
        pixel_size=8, ascent=7, descent=1, bbox=(8, 8, 0, -1),
        glyphs=[Glyph(cp=cp, name=f"uni{cp:04X}", dwidth=8, bbw=8, bbh=8,
                      bbx=0, bby=-1, rows=bitmap) for cp, bitmap in sorted(rows.items())],
        warnings=warnings or [],
    )


def convert_tmat(path: Path, slug: str) -> ParsedFont:
    text = path.read_text(encoding="utf-8")
    blocks = re.findall(
        r"\{\s*//\s*(\d+)\s*\(0x([0-9a-fA-F]+)\)[^\n]*\n"
        r"((?:\s*0b[01]{8},?\s*\n){8})\s*\}", text,
    )
    rows = {}
    for decimal, hexadecimal, body in blocks:
        cp = int(decimal)
        if cp != int(hexadecimal, 16) or cp in rows:
            raise ValueError(f"{path}: inconsistent/duplicate code point {decimal}")
        rows[cp] = bytes(int(n, 2) for n in re.findall(r"0b([01]{8})", body))
    if set(rows) != set(range(32, 128)):
        raise ValueError(f"{path}: expected all 96 entries U+0020–U+007F")
    return _font(path, slug, rows, "Copyright (C) 2020, Takayuki Matsuoka. CC0-1.0")


def convert_font8x8(path: Path, slug: str) -> ParsedFont:
    rows: dict[int, bytes] = {}
    seen: set[Path] = set()
    warnings: list[str] = []

    def read(header: Path):
        if header in seen:
            return
        seen.add(header)
        text = header.read_text(encoding="utf-8")
        for include in re.findall(r'^\s*#include "([^"/]+)"', text, re.M):
            read(header.parent / include)
        array = re.search(r'char\s+font8x8_\w+\[(\d+)\]\[8\]\s*=\s*\{(.*?)\};', text, re.S)
        if not array:
            if '#include' not in text:
                raise ValueError(f"{header}: missing bitmap table")
            return
        cells = re.findall(r'\{([^{}]*)\}\s*,?\s*//([^\n]*)', array[2])
        if len(cells) != int(array[1]):
            raise ValueError(f"{header}: incomplete bitmap table")
        span = re.search(r'unicode points U\+([0-9A-Fa-f]+)\s*-\s*U\+([0-9A-Fa-f]+)', text)
        if span and int(span[2], 16) - int(span[1], 16) + 1 != len(cells):
            raise ValueError(f"{header}: code point range does not match table size")
        for i, (body, comment) in enumerate(cells):
            values = re.findall(r'0x([0-9A-Fa-f]{2})\b', body)
            if len(values) != 8:
                raise ValueError(f"{header}: row {i} is not eight bytes")
            if span:
                # Indexed ranges are authoritative: Greek's comments mistakenly
                # repeat U+0399/U+03A5 for the diaeresis glyphs U+03AA/U+03AB.
                cp = int(span[1], 16) + i
            else:
                encoded = re.search(r'U\+([0-9A-Fa-f]{4,6})\b', comment)
                if not encoded:
                    warnings.append(f"{header.name} row {i}: no upstream Unicode mapping; skipped")
                    continue
                cp = int(encoded[1], 16)
            bitmap = bytes(_REVERSE[int(n, 16)] for n in values)
            if cp in rows and rows[cp] != bitmap:
                raise ValueError(f"{header}: conflicting bitmaps for U+{cp:04X}")
            rows[cp] = bitmap

    read(path)
    return _font(path, slug, rows, "Marcel Sondaar; IBM public-domain VGA fonts; C headers by Daniel Hepper. Public Domain.", warnings)
