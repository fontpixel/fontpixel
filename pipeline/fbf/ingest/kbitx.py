"""kbitx(Bits'n'Picas XML)→ ParsedFont。

`d` 属性 = base64([height u8][width u8] + 操作码流),按行主序:
  0x01–0x3F      跳过 N 个透明像素
  0x40+N (≤0x7F) 画 N 个实心像素
  0x80+N (≤0xBF) 后随 1 字节灰度,重复 N 次
  0xC0+N         后随 N 字节逐像素灰度
灰度 ≥0x80 视为点亮。已用 galmuri kbitx/BDF 双发布逐像素验证。
"""

from __future__ import annotations

import base64
import xml.etree.ElementTree as ET
from pathlib import Path

from fbf.model import Glyph, ParsedFont, row_bytes


def _decode_bitmap(data: str, warnings: list[str], label: str
                   ) -> tuple[int, int, bytes] | None:
    raw = base64.b64decode(data + "=" * (-len(data) % 4))
    if len(raw) < 2:
        return None
    h, w = raw[0], raw[1]
    if w == 0 or h == 0:
        return None
    bits = bytearray(w * h)
    pos = 0
    i = 2
    total = w * h
    while i < len(raw) and pos < total:
        op = raw[i]
        i += 1
        if op < 0x40:
            pos += op
        elif op < 0x80:
            n = op - 0x40
            for _ in range(n):
                if pos < total:
                    bits[pos] = 1
                pos += 1
        elif op < 0xC0:
            n = op - 0x80
            if i >= len(raw):
                break
            v = raw[i]
            i += 1
            for _ in range(n):
                if pos < total and v >= 0x80:
                    bits[pos] = 1
                pos += 1
        else:
            n = op - 0xC0
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
