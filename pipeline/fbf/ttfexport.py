"""把同一字体的多个点阵尺寸打包成单个位图 TTF(EBDT/EBLC strike)。

产物只含位图,不含矢量轮廓:glyf 里每个字形都是空轮廓,真正的形状全在
EBDT 的各 ppem strike 里。这样一个文件就覆盖了该字体的全部尺寸,
支持位图 strike 的渲染器(FreeType、macOS、多数 Linux 桌面)可直接使用。
"""

from __future__ import annotations

from pathlib import Path

from fbf.model import ParsedFont, row_bytes

UPEM = 1000


def glyph_name(cp: int) -> str:
    return f"uni{cp:04X}" if cp <= 0xFFFF else f"u{cp:05X}"


def _clamp8(v: int) -> int:
    return max(-128, min(127, v))


def build_ttf(fonts: list[ParsedFont], family_name: str, style_name: str,
              out: Path, *, copyright_: str = "", version: str = "1.000") -> dict:
    """fonts:同一字体的不同尺寸(每个 ParsedFont 一个 strike)。"""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.ttLib import newTable
    from fontTools.ttLib.tables import E_B_D_T_, E_B_L_C_
    from fontTools.ttLib.tables.BitmapGlyphMetrics import SmallGlyphMetrics

    if not fonts:
        raise ValueError("没有可导出的字体")
    fonts = sorted(fonts, key=lambda f: f.pixel_size)
    ref = fonts[-1]  # 以最大尺寸作为矢量度量的参照

    cps = sorted({g.cp for f in fonts for g in f.glyphs})
    if not cps:
        raise ValueError("没有字形")
    order = [".notdef"] + [glyph_name(cp) for cp in cps]

    fb = FontBuilder(UPEM, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({cp: glyph_name(cp) for cp in cps})
    # 空轮廓:形状全部来自位图 strike
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    empty = TTGlyphPen(None).glyph()
    fb.setupGlyf({name: empty for name in order})

    ref_by_cp = {g.cp: g for g in ref.glyphs}
    scale = UPEM / max(ref.pixel_size, 1)
    metrics = {".notdef": (int(round(ref.pixel_size * scale / 2)), 0)}
    for cp in cps:
        g = ref_by_cp.get(cp)
        if g is None:  # 该尺寸缺字时退回其它尺寸按比例换算
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
    fb.setupNameTable({
        "familyName": family_name,
        "styleName": style_name,
        "uniqueFontIdentifier": f"{family_name}-{style_name}-{version}",
        "fullName": f"{family_name} {style_name}",
        "psName": f"{family_name}-{style_name}".replace(" ", ""),
        "version": version,
        "copyright": copyright_,
    })
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, usWinAscent=asc,
                usWinDescent=abs(desc))
    fb.setupPost(isFixedPitch=0)

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
        bst.flags = 1  # 横排
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
        raise ValueError("没有生成任何 strike")

    font["EBDT"] = ebdt
    font["EBLC"] = eblc
    out.parent.mkdir(parents=True, exist_ok=True)
    font.save(out)
    return {
        "sizes": [f.pixel_size for f in fonts],
        "glyphs": len(cps),
        "strikes": len(eblc.strikes),
    }
