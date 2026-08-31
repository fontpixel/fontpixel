"""OTB (OpenType Bitmap, EBDT/EBLC) → ParsedFont."""

from __future__ import annotations

from pathlib import Path

from opf.model import Glyph, ParsedFont, row_bytes


def convert_otb(path: Path, family_slug: str) -> list[tuple[str, ParsedFont]]:
    """One (suffix, ParsedFont) per strike, suffix like "12px"."""
    from fontTools.ttLib import TTFont

    font = TTFont(path)
    cmap = font.getBestCmap()
    if cmap is None:
        # common in old CJK fonts: a (3,0) Symbol table masquerading as a Unicode table, use it directly
        for t in font["cmap"].tables:
            sub = getattr(t, "cmap", None)
            if sub:
                cmap = dict(sub)
                break
        if cmap and min(cmap) >= 0xF000 and max(cmap) <= 0xF0FF:
            cmap = {cp - 0xF000: g for cp, g in cmap.items()}  # a genuine Symbol table, shift it back
    if not cmap:
        raise ValueError(f"{path}: no usable cmap")
    name_to_cp: dict[str, int] = {}
    for cp, gname in cmap.items():
        # when one glyph name maps to multiple code points, keep the lowest and let the rest share the glyph
        if gname not in name_to_cp or cp < name_to_cp[gname]:
            name_to_cp[gname] = cp

    eblc = font["EBLC"]
    ebdt = font["EBDT"]
    out: list[tuple[str, ParsedFont]] = []
    for si, strike in enumerate(eblc.strikes):
        bst = strike.bitmapSizeTable
        ppem = int(bst.ppemY)
        strike_data = ebdt.strikeData[si]

        glyphs: dict[int, Glyph] = {}
        warnings: list[str] = []
        for cp, gname in cmap.items():
            bg = strike_data.get(gname)
            if bg is None:
                continue
            try:
                m = bg.metrics
            except AttributeError:
                bg.decompile()
                m = bg.metrics
            w, h = int(m.width), int(m.height)
            nb = row_bytes(w)
            rows = bytearray()
            for y in range(h):
                row = bg.getRow(y, bitDepth=1, metrics=m, reverseBytes=False)
                rows += bytes(row).ljust(nb, b"\x00")[:nb]
            adv = int(getattr(m, "Advance", getattr(m, "horiAdvance", w)))
            bearing_x = int(getattr(m, "BearingX", getattr(m, "horiBearingX", 0)))
            bearing_y = int(getattr(m, "BearingY", getattr(m, "horiBearingY", h)))
            glyphs[cp] = Glyph(
                cp=cp, name=gname, dwidth=adv, bbw=w, bbh=h,
                bbx=bearing_x, bby=bearing_y - h, rows=bytes(rows),
            )

        if not glyphs:
            continue
        asc = int(bst.hori.ascender)
        desc = -int(bst.hori.descender)
        # some OTB strikes report a bogus ascender (e.g. wqy 12ppem reports 16): fall back to measuring the actual glyphs
        max_top = max(g.bby + g.bbh for g in glyphs.values())
        max_bottom = max(-g.bby for g in glyphs.values())
        if asc + desc > ppem * 1.4 or asc < max_top - 1:
            warnings.append(
                f"strike {ppem}px ascender/descender ({asc}/{desc}) 异常,按字形实测取值"
            )
        if asc + desc > ppem * 1.4:
            asc, desc = max_top, max(max_bottom, 0)

        xoff = min(g.bbx for g in glyphs.values())
        yoff = min(g.bby for g in glyphs.values())
        bw = max(g.bbx + g.bbw for g in glyphs.values()) - xoff
        bh = max(g.bby + g.bbh for g in glyphs.values()) - yoff
        pf = ParsedFont(
            path=path,
            family_slug=family_slug,
            file_name=f"{path.stem}-{ppem}px.bdf",
            props={"FONT": f"{path.stem}-{ppem}px", "PIXEL_SIZE": ppem},
            pixel_size=ppem,
            ascent=asc,
            descent=desc,
            bbox=(bw, bh, xoff, yoff),
            glyphs=[glyphs[cp] for cp in sorted(glyphs)],
            warnings=warnings,
        )
        out.append((f"{ppem}px", pf))
    return out
