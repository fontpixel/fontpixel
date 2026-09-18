"""kbitx (Bits'n'Picas XML) → ParsedFont.

`d` attribute = base64([height ULEB128][width ULEB128] + WIB opcode stream),
row-major order. The low five opcode bits give the run length; bit 0x20
multiplies it by 32. The high two bits select transparent (0x00), solid
(0x40), repeated grayscale byte (0x80), or literal grayscale bytes (0xC0).
A grayscale value >=0x80 counts as lit. See Bits'N'Picas'
KbitxBitmapFontImporter and WIBInputStream for the source format.
"""

from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from pathlib import Path

from opf.model import Glyph, ParsedFont, row_bytes


def _read_uleb128(raw: bytes, offset: int) -> tuple[int, int]:
    value = shift = 0
    while offset < len(raw):
        byte = raw[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ValueError("truncated bitmap dimension")


def _decode_bitmap(data: str, warnings: list[str], label: str
                   ) -> tuple[int, int, bytes] | None:
    raw = base64.b64decode(data + "=" * (-len(data) % 4))
    if len(raw) < 2:
        return None
    try:
        h, i = _read_uleb128(raw, 0)
        w, i = _read_uleb128(raw, i)
    except ValueError as error:
        warnings.append(f"{label}: {error}")
        return None
    if w == 0 or h == 0:
        return None
    bits = bytearray(w * h)
    pos = 0
    total = w * h
    while i < len(raw) and pos < total:
        op = raw[i]
        i += 1
        n = op & 0x1F
        if op & 0x20:
            n <<= 5
        kind = op & 0xC0
        if kind == 0x00:
            pos += n
        elif kind == 0x40:
            for _ in range(n):
                if pos < total:
                    bits[pos] = 1
                pos += 1
        elif kind == 0x80:
            if i >= len(raw):
                break
            v = raw[i]
            i += 1
            for _ in range(n):
                if pos < total and v >= 0x80:
                    bits[pos] = 1
                pos += 1
        else:
            for k in range(n):
                if i >= len(raw):
                    break
                v = raw[i]
                i += 1
                if pos < total and v >= 0x80:
                    bits[pos] = 1
                pos += 1
    if pos > total:
        warnings.append(f"{label}: bitmap overflow ({pos}>{total})")
    nb = row_bytes(w)
    rows = bytearray(nb * h)
    for y in range(h):
        for x in range(w):
            if bits[y * w + x]:
                rows[y * nb + (x >> 3)] |= 0x80 >> (x & 7)
    return w, h, bytes(rows)


def convert_kbitx(path: Path, family_slug: str) -> ParsedFont:
    root = ET.parse(path).getroot()
    props: dict[str, int] = {}
    for p in root.findall("prop"):
        try:
            props[p.get("id", "")] = int(p.get("value", "0"))
        except ValueError:
            pass
    names = {n.get("id"): n.get("value", "") for n in root.findall("name")}

    ascent = props.get("emAscent", props.get("lineAscent", 0))
    descent = props.get("emDescent", props.get("lineDescent", 0))
    pixel_size = ascent + descent

    warnings: list[str] = []
    glyphs: dict[int, Glyph] = {}
    for g in root.findall("g"):
        u = g.get("u")
        if u is None:
            continue
        try:
            cp = int(u)
        except ValueError:
            continue
        if cp < 0 or cp in glyphs:
            continue
        adv = int(g.get("w", "0"))
        x = int(g.get("x", "0"))
        y = int(g.get("y", "0"))
        decoded = _decode_bitmap(g.get("d", ""), warnings, f"U+{cp:04X}")
        if decoded is None:
            glyphs[cp] = Glyph(cp=cp, name=f"uni{cp:04X}", dwidth=adv,
                               bbw=0, bbh=0, bbx=0, bby=0, rows=b"")
            continue
        w, h, rows = decoded
        glyphs[cp] = Glyph(
            cp=cp, name=f"uni{cp:04X}", dwidth=adv,
            bbw=w, bbh=h, bbx=x, bby=y - h, rows=rows,
        )

    if not glyphs:
        raise ValueError(f"{path}: no glyphs")
    xoff = min(g.bbx for g in glyphs.values())
    yoff = min(g.bby for g in glyphs.values())
    bw = max(g.bbx + g.bbw for g in glyphs.values()) - xoff
    bh = max(g.bby + g.bbh for g in glyphs.values()) - yoff
    font_name = names.get("4") or names.get("1") or path.stem
    copyright_ = names.get("0", "")
    props_out: dict[str, str | int] = {
        "FONT": font_name, "PIXEL_SIZE": pixel_size,
    }
    if copyright_:
        props_out["COPYRIGHT"] = copyright_
    return ParsedFont(
        path=path,
        family_slug=family_slug,
        file_name=f"{path.stem}.bdf",
        props=props_out,
        pixel_size=pixel_size,
        ascent=ascent,
        descent=descent,
        bbox=(bw, bh, xoff, yoff),
        glyphs=[glyphs[cp] for cp in sorted(glyphs)],
        warnings=warnings,
    )
