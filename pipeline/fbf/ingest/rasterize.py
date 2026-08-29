"""矢量化像素字体(TTF/OTF)按原生格点栅格化回点阵。

原生 ppem 判定:轮廓全部坐标对 upem 的公约格点;格点整除 upem 且
ppem 落在 4–64 才认定是矢量化像素字体,否则返回 None(普通轮廓
字体不转制,进导入报告人工定夺)。
"""

from __future__ import annotations

import math
from pathlib import Path

from fbf.model import Glyph, ParsedFont, row_bytes

_SAMPLE_GLYPHS = 300
_MIN_PPEM, _MAX_PPEM = 4, 64


def detect_native_ppem(path: Path) -> int | None:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.ttLib import TTFont

    font = TTFont(path, fontNumber=0)
    upem = font["head"].unitsPerEm
    glyphset = font.getGlyphSet()
    names = list(font.getGlyphOrder())[1:]  # 跳过 .notdef
    step = max(1, len(names) // _SAMPLE_GLYPHS)

    g = 0
    sampled = 0
    for name in names[::step]:
        pen = RecordingPen()
        try:
            glyphset[name].draw(pen)
        except Exception:
            continue
        drew = False
        for op, pts in pen.value:
            if op == "addComponent":
                continue  # 组件引用,坐标随基字形采样
            for pt in pts:
                if not (isinstance(pt, tuple) and len(pt) == 2):
                    continue
                x, y = pt
                if x != int(x) or y != int(y):
                    return None  # 非整数坐标:不是干净的格点字体
                g = math.gcd(g, abs(int(x)))
                g = math.gcd(g, abs(int(y)))
                drew = True
        if drew:
            sampled += 1
        if sampled >= _SAMPLE_GLYPHS:
            break

    if sampled < 20 or g <= 1:
        return None
    if upem % g != 0:
        return None
    ppem = upem // g
    if not (_MIN_PPEM <= ppem <= _MAX_PPEM):
        return None
    return ppem


def _materialize_sfnt(path: Path) -> Path:
    """woff/woff2 → 解包成临时 ttf(freetype 不带 brotli 时无法直读)。"""
    if path.suffix.lower() not in (".woff", ".woff2"):
        return path
    import tempfile

    from fontTools.ttLib import TTFont

    font = TTFont(path)
    font.flavor = None
    tmp = Path(tempfile.mkstemp(suffix=".ttf")[1])
    font.save(tmp)
    return tmp


def rasterize_ttf(path: Path, ppem: int, family_slug: str) -> ParsedFont:
    import freetype

    face = freetype.Face(str(_materialize_sfnt(path)))
    face.set_pixel_sizes(0, ppem)
    flags = (freetype.FT_LOAD_RENDER | freetype.FT_LOAD_MONOCHROME
             | freetype.FT_LOAD_TARGET_MONO)

    glyphs: dict[int, Glyph] = {}
    warnings: list[str] = []
    cp, gindex = face.get_first_char()
    while gindex:
        if cp not in glyphs and cp >= 0x20:
            try:
                face.load_char(cp, flags)
                bm = face.glyph.bitmap
                w, h = bm.width, bm.rows
                nb = row_bytes(w)
                rows = bytearray()
                for y in range(h):
                    row = bytes(bm.buffer[y * bm.pitch : y * bm.pitch + nb])
                    rows += row.ljust(nb, b"\x00")[:nb]
                glyphs[cp] = Glyph(
                    cp=cp,
                    name=f"uni{cp:04X}",
                    dwidth=face.glyph.advance.x >> 6,
                    bbw=w,
                    bbh=h,
                    bbx=face.glyph.bitmap_left,
                    bby=face.glyph.bitmap_top - h,
                    rows=bytes(rows),
                )
            except Exception as e:  # noqa: BLE001 - 单字形失败仅告警
                warnings.append(f"U+{cp:04X}: {e}")
        cp, gindex = face.get_next_char(cp, gindex)

    if not glyphs:
        raise ValueError(f"{path}: rasterization produced no glyphs")

    asc = face.size.ascender >> 6
    desc = -(face.size.descender >> 6)
    max_top = max(g.bby + g.bbh for g in glyphs.values())
    max_bottom = max(-g.bby for g in glyphs.values())
    if asc + desc > ppem * 1.6:
        asc, desc = max_top, max(max_bottom, 0)
        warnings.append("ascender/descender 异常,按字形实测取值")

    xoff = min(g.bbx for g in glyphs.values())
    yoff = min(g.bby for g in glyphs.values())
    bw = max(g.bbx + g.bbw for g in glyphs.values()) - xoff
    bh = max(g.bby + g.bbh for g in glyphs.values()) - yoff
    return ParsedFont(
        path=path,
        family_slug=family_slug,
        file_name=f"{path.stem}-{ppem}px.bdf",
        props={"FONT": f"{path.stem}-{ppem}px", "PIXEL_SIZE": ppem},
        pixel_size=ppem,
        ascent=asc,
        descent=desc,
        bbox=(bw, bh, xoff, yoff),
        glyphs=[glyphs[c] for c in sorted(glyphs)],
        warnings=warnings,
    )
