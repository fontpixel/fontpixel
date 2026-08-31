"""把点阵字形转成矢量轮廓 TTF:每个亮起的像素画成一个方块或圆点。

与 `ttfexport` 的位图 TTF 不同,这里生成的是真正的矢量字体(有 glyf 轮廓),
任何渲染器、任何字号都能用,代价是文件更大、放大后仍是像素造型(这正是要的效果)。

两种造型:
    square  每个像素一个正方形。相邻像素会合并成矩形条带以减少轮廓点数。
    round   每个像素一个圆点(四段二次贝塞尔近似)。圆本身只存一份,
            各字形以复合字形(composite glyph)引用它,只存偏移量。

一个字体一个尺寸——矢量字体没有 strike 概念,所以同一家族的每个像素尺寸
各出一个 TTF;字号缩放由渲染器完成。
"""

from __future__ import annotations

from pathlib import Path

from opf.model import ParsedFont, row_bytes

UPEM = 1000


def _lit_rows(glyph) -> list[list[bool]]:
    nb = row_bytes(glyph.bbw)
    return [
        [bool(glyph.rows[y * nb + (x >> 3)] & (0x80 >> (x & 7)))
         for x in range(glyph.bbw)]
        for y in range(glyph.bbh)
    ]


def _runs(row: list[bool]) -> list[tuple[int, int]]:
    """一行里连续亮像素的 [start, end) 区间。"""
    out: list[tuple[int, int]] = []
    x = 0
    while x < len(row):
        if row[x]:
            s = x
            while x < len(row) and row[x]:
                x += 1
            out.append((s, x))
        else:
            x += 1
    return out


def _rects(rows: list[list[bool]]) -> list[tuple[int, int, int, int]]:
    """把亮像素合并成矩形:先按行取游程,再把上下相同的游程纵向合并。

    返回 (x, y_top, width, height),y 以位图顶部为 0。
    """
    pending: dict[tuple[int, int], tuple[int, int]] = {}  # (s,e) -> (y_top, h)
    out: list[tuple[int, int, int, int]] = []
    for y, row in enumerate(rows):
        cur = dict.fromkeys(_runs(row), True)
        for key in list(pending):
            if key in cur:
                y0, h = pending[key]
                pending[key] = (y0, h + 1)
                del cur[key]
            else:
                y0, h = pending.pop(key)
                out.append((key[0], y0, key[1] - key[0], h))
        for key in cur:
            pending[key] = (y, 1)
    for key, (y0, h) in pending.items():
        out.append((key[0], y0, key[1] - key[0], h))
    return out


def _draw_square(pen, glyph, unit: int, baseline_top: int) -> None:
    for x, ytop, w, h in _rects(_lit_rows(glyph)):
        x0 = (glyph.bbx + x) * unit
        x1 = x0 + w * unit
        y1 = (baseline_top - ytop) * unit
        y0 = y1 - h * unit
        pen.moveTo((x0, y0))
        pen.lineTo((x1, y0))
        pen.lineTo((x1, y1))
        pen.lineTo((x0, y1))
        pen.closePath()


DOT = "dot"  # 圆点版的基准字形名


def _dot_glyph(unit: int):
    """位于 (0,0)-(unit,unit) 的一个圆,供所有字形以复合字形复用。

    用 TrueType 原生的二次贝塞尔,4 段(8 个点)。控制点取 0.9142r 而不是
    外接方角的 r——这样弧线中点正好落在圆上,径向误差约 2%,肉眼就是个圆。
    """
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    r = unit / 2
    c = 0.9142135623730951 * r  # 使弧中点落在圆上的控制点偏移
    cx = cy = r
    pen = TTGlyphPen(None)
    pen.moveTo((cx + r, cy))
    pen.qCurveTo((cx + c, cy + c), (cx, cy + r))
    pen.qCurveTo((cx - c, cy + c), (cx - r, cy))
    pen.qCurveTo((cx - c, cy - c), (cx, cy - r))
    pen.qCurveTo((cx + c, cy - c), (cx + r, cy))
    pen.closePath()
    return pen.glyph()


def _place_dots(pen, glyph, unit: int, baseline_top: int) -> None:
    """每个亮像素放一个指向 DOT 的复合字形组件。

    存一份圆的轮廓、其余只存偏移量,比每个像素各存一整圈轮廓小三倍多——
    点阵字体动辄几十万个点,这直接决定文件大小。
    """
    for y, row in enumerate(_lit_rows(glyph)):
        for x, on in enumerate(row):
            if on:
                pen.addComponent(DOT, (1, 0, 0, 1, (glyph.bbx + x) * unit,
                                       (baseline_top - y - 1) * unit))


def build_vector_ttf(font: ParsedFont, family_name: str, style_name: str,
                     out: Path, *, shape: str = "square",
                     copyright_: str = "", version: str = "1.000") -> dict:
    """一个点阵字体 → 一个矢量 TTF。shape 为 "square" 或 "round"。"""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    if shape not in ("square", "round"):
        raise ValueError(f"未知造型 {shape}")
    if not font.glyphs:
        raise ValueError("没有字形")

    unit = UPEM // max(font.pixel_size, 1)
    if unit < 1:
        raise ValueError(f"像素尺寸 {font.pixel_size} 超出 upem {UPEM}")
    upem = unit * font.pixel_size  # 取整后的实际 em,保证像素对齐
    baseline_top_of = lambda g: g.bby + g.bbh  # noqa: E731

    from opf.ttfexport import FIXED_TIMESTAMP, glyph_name, name_records

    round_ = shape == "round"
    by_cp = {g.cp: g for g in font.glyphs}
    cps = sorted(by_cp)
    order = [".notdef"] + ([DOT] if round_ else []) + [glyph_name(cp) for cp in cps]

    fb = FontBuilder(upem, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({cp: glyph_name(cp) for cp in cps})

    draw = _place_dots if round_ else _draw_square
    glyphs = {".notdef": TTGlyphPen(None).glyph()}
    metrics = {".notdef": (max(unit * font.pixel_size // 2, 1), 0)}
    if round_:
        glyphs[DOT] = _dot_glyph(unit)
        metrics[DOT] = (unit, 0)
    # 复合字形要能查到被引用的基准字形才能算出外框
    gs = {DOT: glyphs[DOT]} if round_ else None
    for cp in cps:
        g = by_cp[cp]
        pen = TTGlyphPen(gs)
        if g.bbw and g.bbh:
            draw(pen, g, unit, baseline_top_of(g))
        glyphs[glyph_name(cp)] = pen.glyph()
        metrics[glyph_name(cp)] = (max(g.dwidth, 0) * unit, g.bbx * unit)
    fb.setupGlyf(glyphs)
    # hmtx 的 lsb 必须等于轮廓的 xMin：TrueType 渲染器按二者之差平移字形，
    # 写成 bbx 会让「（」这类墨迹靠右的字形整体左移、撞进前一个字。
    # 组合字形（round 的点阵引用）也要经 recalcBounds 展开后取实际边界。
    glyf_table = fb.font["glyf"]
    for name in order:
        gl = glyf_table[name]
        gl.recalcBounds(glyf_table)
        adv, _ = metrics[name]
        metrics[name] = (adv, getattr(gl, "xMin", 0))
    fb.setupHorizontalMetrics(metrics)

    asc = font.ascent * unit
    desc = -font.descent * unit
    fb.setupHorizontalHeader(ascent=asc, descent=desc)
    fb.setupNameTable(name_records(family_name, style_name, copyright_, version))
    fb.setupOS2(sTypoAscender=asc, sTypoDescender=desc, usWinAscent=asc,
                usWinDescent=abs(desc))
    fb.setupPost(keepGlyphNames=False, isFixedPitch=0)
    out.parent.mkdir(parents=True, exist_ok=True)
    head = fb.font["head"]
    head.created = head.modified = FIXED_TIMESTAMP
    fb.save(out)
    return {"shape": shape, "glyphs": len(cps), "upem": upem,
            "pixelSize": font.pixel_size}
