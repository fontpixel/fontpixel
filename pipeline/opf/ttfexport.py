"""Pack multiple bitmap sizes of the same font into a single bitmap TTF (EBDT/EBLC strikes).

Output holds only bitmaps, no vector outlines: every glyph in glyf is an
empty outline, and the actual shapes live entirely in EBDT's per-ppem
strikes. This way one file covers every size of the font, and any
renderer that supports bitmap strikes (FreeType, macOS, most Linux
desktops) can use it directly.
"""

from __future__ import annotations

from pathlib import Path

from opf.model import ParsedFont, row_bytes

UPEM = 1000
# Fixed head timestamp (2020-01-01, seconds since the 1904 epoch). The
# same input must produce the same bytes, or every build would have CI
# re-upload every TTF all over again.
FIXED_TIMESTAMP = 3660681600
MAX_GLYPHS = 65535  # TTF glyph count limit (including .notdef)


def name_records(family: str, style: str, copyright_: str,
                 version: str = "1.000") -> dict[str, str]:
    """Contents of the TTF name table.

    Shared by three call sites: bitmap export, vector export, and the
    cache-hit "metadata refresh only" path
    (downloads.refresh_downloads_metadata). Writing it in more than one
    place would make the fast path's output bytes diverge from a full rebuild.
    """
    return {
        "familyName": family,
        "styleName": style,
        "uniqueFontIdentifier": f"{family}-{style}-{version}",
        "fullName": f"{family} {style}",
        "psName": f"{family}-{style}".replace(" ", ""),
        "version": version,
        "copyright": copyright_,
    }


def glyph_name(cp: int) -> str:
    return f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"


def _clamp8(v: int) -> int:
    return max(-128, min(127, v))


def build_ttf(fonts: list[ParsedFont], family_name: str, style_name: str,
              out: Path, *, copyright_: str = "", version: str = "1.000") -> dict:
    """fonts: different sizes of the same font (one ParsedFont per strike)."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables import E_B_D_T_, E_B_L_C_
    from fontTools.ttLib.tables.BitmapGlyphMetrics import SmallGlyphMetrics

    if not fonts:
        raise ValueError("no fonts to export")
    fonts = sorted(fonts, key=lambda f: f.pixel_size)
    ref = fonts[-1]  # use the largest size as the reference for vector metrics

    cps = sorted({g.cp for f in fonts for g in f.glyphs})
    if not cps:
        raise ValueError("no glyphs")
    if len(cps) + 1 > MAX_GLYPHS:
        raise ValueError(
            f"{len(cps)} glyphs exceed the TTF limit of {MAX_GLYPHS - 1}; export each variant separately")
    order = [".notdef"] + [glyph_name(cp) for cp in cps]

    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({cp: glyph_name(cp) for cp in cps})
    # Empty outlines: shapes come entirely from the bitmap strikes
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    empty = TTGlyphPen(None).glyph()
    fb.setupGlyf({name: empty for name in order})

    ref_by_cp = {g.cp: g for g in ref.glyphs}
    scale = UPEM / max(ref.pixel_size, 1)
    metrics = {".notdef": (int(round(ref.pixel_size * scale / 2)), 0)}
    for cp in cps:
        g = ref_by_cp.get(cp)
        if g is None:  # if missing at this size, fall back to another size and scale proportionally
            for f in reversed(fonts):
                other = next((x for x in f.glyphs if x.cp == cp), None)
                if other is not None:
                    metrics[glyph_name(cp)] = (
                        int(round(other.dwidth * UPEM / max(f.pixel_size, 1))), 0)
                    break
            else:
                metrics[glyph_name(cp)] = (0, 0)
        else:
            metrics[glyph_name(cp)] = (int(round(g.dwidth * scale)), 0)
    fb.setupHorizontalMetrics(metrics)

    asc = int(round(ref.ascent * scale))
    desc = int(round(-ref.descent * scale))
    fb.setupHorizontalHeader(ascent=asc, descent=desc)
    fb.setupNameTable(name_records(family_name, style_name, copyright_, version))
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, usWinAscent=asc,
                usWinDescent=abs(desc))
    # Bitmap fonts don't need glyph names; post 2.0 stores names via a 16-bit index, which overflows at 65K glyphs
    fb.setupPost(keepGlyphNames=False, isFixedPitch=0)

    font = fb.font
    eblc = newTable("EBLC")
    ebdt = newTable("EBDT")
    eblc.version = 2.0
    ebdt.version = 2.0
    eblc.strikes = []
    ebdt.strikeData = []

    for f in fonts:
        by_cp = {g.cp: g for g in f.glyphs}
        data: dict[str, object] = {}
        for cp in cps:
            g = by_cp.get(cp)
            if g is None:
                continue
            bm = E_B_D_T_.ebdt_bitmap_format_1(b"", font)
            m = SmallGlyphMetrics()
            m.height = g.bbh
            m.width = g.bbw
            m.BearingX = _clamp8(g.bbx)
            m.BearingY = _clamp8(g.bby + g.bbh)
            m.Advance = max(0, min(255, g.dwidth))
            bm.metrics = m
            bm.imageData = g.rows if g.rows else b"\x00" * max(
                1, g.bbh * row_bytes(g.bbw))
            data[glyph_name(cp)] = bm
        if not data:
            continue

        strike = E_B_L_C_.Strike()
        bst = E_B_L_C_.BitmapSizeTable()
        for direction in ("hori", "vert"):
            lm = E_B_L_C_.SbitLineMetrics()
            lm.ascender = f.ascent
            lm.descender = -f.descent
            lm.widthMax = max((g.dwidth for g in f.glyphs), default=f.pixel_size)
            lm.caretSlopeNumerator = 0
            lm.caretSlopeDenominator = 1
            lm.caretOffset = 0
            lm.minOriginSB = 0
            lm.minAdvanceSB = 0
            lm.maxBeforeBL = 0
            lm.minAfterBL = 0
            lm.pad1 = 0
            lm.pad2 = 0
            setattr(bst, direction, lm)
        bst.colorRef = 0
        bst.startGlyphIndex = 0
        bst.endGlyphIndex = len(order) - 1
        bst.ppemX = f.pixel_size
        bst.ppemY = f.pixel_size
        bst.bitDepth = 1
        bst.flags = 1  # horizontal layout
        strike.bitmapSizeTable = bst

        ist = E_B_L_C_.eblc_index_sub_table_1(b"", font)
        ist.indexFormat = 1
        ist.imageFormat = 1
        ist.imageDataOffset = 0
        ist.names = [n for n in order if n in data]
        strike.indexSubTables = [ist]

        eblc.strikes.append(strike)
        ebdt.strikeData.append(data)

    if not eblc.strikes:
        raise ValueError("no strikes were generated")

    font["EBDT"] = ebdt
    font["EBLC"] = eblc
    out.parent.mkdir(parents=True, exist_ok=True)
    font["head"].created = font["head"].modified = FIXED_TIMESTAMP
    font.save(out)
    return {
        "sizes": [f.pixel_size for f in fonts],
        "glyphs": len(cps),
        "strikes": len(eblc.strikes),
    }
