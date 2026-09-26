"""Convert bitmap glyphs into a vector-outline TTF: each lit pixel is drawn as a square or a dot.

Unlike `ttfexport`'s bitmap TTF, this produces a genuine vector font (with
glyf outlines) usable by any renderer at any size, at the cost of a
larger file — and it still looks pixelated when scaled up, which is the
intended effect.

Two shapes:
    square  One square per pixel. Adjacent pixels are merged into
            rectangular strips to reduce outline point count.
    round   One dot per pixel (approximated with four quadratic Bézier
            segments). The circle itself is stored only once; each glyph
            references it as a composite glyph, storing only an offset.

One font per size — vector fonts have no notion of a strike, so each
pixel size within a family gets its own TTF; scaling to a display size is
left to the renderer.
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
    """The [start, end) interval of consecutive lit pixels in one row."""
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
    """Merge lit pixels into rectangles: take runs row by row, then merge vertically-matching runs across rows.

    Returns (x, y_top, width, height), with y measured from the top of the bitmap (0).
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


def _contours(rows: list[list[bool]]) -> list[list[tuple[int, int]]]:
    """Trace the outline of every connected run of lit pixels.

    One closed polygon per boundary — outer edges and the edges around any
    hole — with a point only where the boundary actually turns. That beats
    emitting one rectangle per pixel strip (the older approach): a CJK glyph
    of solid strokes collapses to a couple of polygons instead of dozens of
    abutting rectangles, which is most of the outline-point cost of a
    vectorised bitmap font.

    Each lit pixel contributes a directed unit edge wherever its neighbour is
    unlit, always oriented so the ink lies on the same side. Chaining those
    edges head-to-tail therefore closes loops whose winding is automatically
    opposite for holes, which is exactly what the nonzero fill rule wants.
    Where two regions meet at a corner the vertex has two outgoing edges;
    always turning as far as possible towards the ink keeps them as two
    touching loops rather than one figure of eight through the shared point.

    Points come back in bitmap coordinates, y measured from the top.
    """
    h, w = len(rows), len(rows[0]) if rows else 0
    lit = lambda x, y: 0 <= x < w and 0 <= y < h and rows[y][x]

    # start point -> end point, for each directed boundary edge
    edges: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for y in range(h):
        for x in range(w):
            if not rows[y][x]:
                continue
            if not lit(x, y - 1):
                edges.setdefault((x, y), []).append((x + 1, y))
            if not lit(x + 1, y):
                edges.setdefault((x + 1, y), []).append((x + 1, y + 1))
            if not lit(x, y + 1):
                edges.setdefault((x + 1, y + 1), []).append((x, y + 1))
            if not lit(x - 1, y):
                edges.setdefault((x, y + 1), []).append((x, y))

    out: list[list[tuple[int, int]]] = []
    while edges:
        start = next(iter(edges))
        pt = start
        poly: list[tuple[int, int]] = []
        prev_d: tuple[int, int] | None = None
        while True:
            outgoing = edges.get(pt)
            if not outgoing:
                break
            if len(outgoing) == 1 or prev_d is None:
                nxt = outgoing[0]
            else:
                # Sharpest right turn first, so touching corners stay separate
                px, py = prev_d
                order = [(-py, px), (px, py), (py, -px)]  # hug the ink: left, straight, right
                nxt = min(
                    outgoing,
                    key=lambda e: order.index((e[0] - pt[0], e[1] - pt[1]))
                    if (e[0] - pt[0], e[1] - pt[1]) in order else 3,
                )
            outgoing.remove(nxt)
            if not outgoing:
                del edges[pt]
            d = (nxt[0] - pt[0], nxt[1] - pt[1])
            if d != prev_d:          # keep corners only, drop collinear points
                poly.append(pt)
            prev_d = d
            pt = nxt
            if pt == start:
                break
        # The loop closed on the starting point; if that point is collinear the
        # first entry is redundant.
        if len(poly) > 2:
            first_d = (poly[1][0] - poly[0][0], poly[1][1] - poly[0][1])
            first_d = (_sign(first_d[0]), _sign(first_d[1]))
            if first_d == prev_d:
                poly.pop(0)
            out.append(poly)
    return out


def _sign(v: int) -> int:
    return (v > 0) - (v < 0)


def _draw_square(pen, glyph, unit: int, baseline_top: int) -> None:
    rows = _lit_rows(glyph)
    if not rows:
        return
    polys = [
        [((glyph.bbx + x) * unit, (baseline_top - y) * unit) for x, y in poly]
        for poly in _contours(rows)
    ]
    # Bitmap y runs down and font y runs up, so the conversion above mirrors
    # every loop. Flip them back when needed: TrueType wants outer contours
    # clockwise, i.e. a negative total signed area with y pointing up.
    if sum(_signed_area(p) for p in polys) > 0:
        polys = [p[::-1] for p in polys]
    for poly in polys:
        pen.moveTo(poly[0])
        for pt in poly[1:]:
            pen.lineTo(pt)
        pen.closePath()


def _signed_area(poly: list[tuple[int, int]]) -> int:
    """Twice the signed area (shoelace); positive means counter-clockwise."""
    total = 0
    for i, (x0, y0) in enumerate(poly):
        x1, y1 = poly[(i + 1) % len(poly)]
        total += x0 * y1 - x1 * y0
    return total


DOT = "dot"  # base glyph name for the round variant


def _dot_glyph(unit: int):
    """A circle at (0,0)-(unit,unit), reused by every glyph as a composite glyph.

    Uses native TrueType quadratic Béziers, 4 segments (8 points). The
    control point is taken at 0.9142r rather than the circumscribing r —
    this makes the arc midpoint land exactly on the circle, with about 2%
    radial error, indistinguishable from a circle to the eye.
    """
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    r = unit / 2
    c = 0.9142135623730951 * r  # control-point offset that puts the arc midpoint on the circle
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
    """Place one component referencing DOT for each lit pixel.

    Storing one circle outline and only offsets for the rest is over
    three times smaller than storing a full outline per pixel — bitmap
    fonts routinely have hundreds of thousands of dots, so this directly
    drives file size.
    """
    for y, row in enumerate(_lit_rows(glyph)):
        for x, on in enumerate(row):
            if on:
                pen.addComponent(DOT, (1, 0, 0, 1, (glyph.bbx + x) * unit,
                                       (baseline_top - y - 1) * unit))


def build_vector_ttf(font: ParsedFont, family_name: str, style_name: str,
                     out: Path, *, shape: str = "square",
                     copyright_: str = "", version: str = "1.000") -> dict:
    """One bitmap font → one vector TTF. shape is "square" or "round"."""
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen

    if shape not in ("square", "round"):
        raise ValueError(f"unknown shape {shape}")
    if not font.glyphs:
        raise ValueError("no glyphs")

    unit = UPEM // max(font.pixel_size, 1)
    if unit < 1:
        raise ValueError(f"pixel size {font.pixel_size} exceeds upem {UPEM}")
    upem = unit * font.pixel_size  # the actual em after rounding, ensuring pixel alignment
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
    # A composite glyph needs its referenced base glyph available to compute its bounding box
    gs = {DOT: glyphs[DOT]} if round_ else None
    for cp in cps:
        g = by_cp[cp]
        pen = TTGlyphPen(gs)
        if g.bbw and g.bbh:
            draw(pen, g, unit, baseline_top_of(g))
        glyphs[glyph_name(cp)] = pen.glyph()
        metrics[glyph_name(cp)] = (max(g.dwidth, 0) * unit, g.bbx * unit)
    fb.setupGlyf(glyphs)
    # hmtx's lsb must equal the outline's xMin: TrueType renderers shift
    # the glyph by their difference, and writing bbx there would push a
    # glyph with right-set ink — like "（" — left as a whole, into the
    # previous character. Composite glyphs (round's dot references) also
    # need recalcBounds expanded to get their actual bounds.
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
