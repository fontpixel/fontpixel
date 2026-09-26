"""OTB (OpenType Bitmap, EBDT/EBLC) → ParsedFont."""

from __future__ import annotations

from pathlib import Path

from opf.model import Glyph, ParsedFont, row_bytes


def convert_otb(path: Path, family_slug: str, *, all_glyphs: bool = False) -> list[tuple[str, ParsedFont]]:
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
        shared_metrics = {
            name: sub.metrics
            for sub in strike.indexSubTables if hasattr(sub, "metrics")
            for name in sub.names
        }

        glyphs: dict[int, Glyph] = {}
        warnings: list[str] = []
        entries = list(cmap.items())
        if all_glyphs:
            encoded_names = set(cmap.values())
            entries.extend((-1, name) for name in font.getGlyphOrder()
                           if name in strike_data and name not in encoded_names)
        unencoded: list[Glyph] = []
        for cp, gname in entries:
            bg = strike_data.get(gname)
            if bg is None:
                continue
            try:
                m = bg.metrics
            except AttributeError:
                # EBDT format 5 stores metrics once in its EBLC index subtable.
                # Accessing a lazy glyph already decompiles it; doing so again
                # would try to consume a data buffer that no longer exists.
                if gname not in shared_metrics:
                    raise ValueError(f"{path}: missing bitmap metrics for {gname}")
                m = shared_metrics[gname]
            w, h = int(m.width), int(m.height)
            nb = row_bytes(w)
            rows = bytearray()
            for y in range(h):
                row = bg.getRow(y, bitDepth=1, metrics=m, reverseBytes=False)
                rows += bytes(row).ljust(nb, b"\x00")[:nb]
            adv = int(getattr(m, "Advance", getattr(m, "horiAdvance", w)))
            bearing_x = int(getattr(m, "BearingX", getattr(m, "horiBearingX", 0)))
            bearing_y = int(getattr(m, "BearingY", getattr(m, "horiBearingY", h)))
            glyph = Glyph(
                cp=cp, name=gname, dwidth=adv, bbw=w, bbh=h,
                bbx=bearing_x, bby=bearing_y - h, rows=bytes(rows),
            )
            if cp == -1:
                unencoded.append(glyph)
            else:
                glyphs[cp] = glyph

        if not glyphs:
            continue
        asc = int(bst.hori.ascender)
        desc = -int(bst.hori.descender)
        # some OTB strikes report a bogus ascender (e.g. wqy 12ppem reports 16): fall back to measuring the actual glyphs
        all_bitmaps = [*glyphs.values(), *unencoded]
        max_top = max(g.bby + g.bbh for g in all_bitmaps)
        max_bottom = max(-g.bby for g in all_bitmaps)
        if asc + desc > ppem * 1.4 or asc < max_top - 1:
            warnings.append(
                f"strike {ppem}px ascender/descender ({asc}/{desc}) implausible, measured from the glyphs instead"
            )
        if asc + desc > ppem * 1.4:
            asc, desc = max_top, max(max_bottom, 0)

        xoff = min(g.bbx for g in all_bitmaps)
        yoff = min(g.bby for g in all_bitmaps)
        bw = max(g.bbx + g.bbw for g in all_bitmaps) - xoff
        bh = max(g.bby + g.bbh for g in all_bitmaps) - yoff
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
            unencoded_glyphs=unencoded,
        )
        out.append((f"{ppem}px", pf))
    return out
