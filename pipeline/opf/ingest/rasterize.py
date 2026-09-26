"""Rasterize a vectorized pixel font (TTF/OTF) back to a bitmap at its native grid.

Native ppem detection: all outline coordinates must share a common grid
divisor of upem; it's only treated as a vectorized pixel font if the grid
evenly divides upem and the resulting ppem falls in 4-64, otherwise returns
None (a regular outline font isn't converted — it's flagged in the import
report for manual review).
"""

from __future__ import annotations

import math
from pathlib import Path

from opf.model import Glyph, ParsedFont, row_bytes

_SAMPLE_GLYPHS = 300
_MIN_PPEM, _MAX_PPEM = 4, 64


def detect_native_ppem(path: Path) -> int | None:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.ttLib import TTFont

    font = TTFont(path, fontNumber=0)
    upem = font["head"].unitsPerEm
    glyphset = font.getGlyphSet()
    names = list(font.getGlyphOrder())[1:]  # skip .notdef
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
                continue  # a component reference; its coordinates are sampled via the base glyph
            for pt in pts:
                if not (isinstance(pt, tuple) and len(pt) == 2):
                    continue
                x, y = pt
                if x != int(x) or y != int(y):
                    return None  # non-integer coordinates: not a clean grid-aligned font
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
    """woff/woff2 → unpack to a temp ttf (freetype can't read them directly without brotli support)."""
    if path.suffix.lower() not in (".woff", ".woff2"):
        return path
    import tempfile

    from fontTools.ttLib import TTFont

    font = TTFont(path)
    font.flavor = None
    tmp = Path(tempfile.mkstemp(suffix=".ttf")[1])
    font.save(tmp)
    return tmp


def rasterize_ttf(path: Path, ppem: int, family_slug: str,
                  hinting: bool = False, *, all_glyphs: bool = False,
                  axes: dict[str, float] | None = None,
                  glyph_offsets: dict[str, list[float]] | None = None,
                  pixel_offset: list[float] | None = None,
                  grid_units: int | None = None) -> ParsedFont:
    import freetype

    origin = pixel_offset if pixel_offset is not None else [0, 0]
    if (len(origin) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float))
                               or not math.isfinite(v) for v in origin)):
        raise ValueError(f"{path}: invalid pixel_offset: {pixel_offset}")

    if grid_units is not None:
        # Some real pixel fonts use an em that is not divisible by their grid
        # (Jersey 10: 1400 upem, 75 units per pixel). Normalize only the in-memory
        # em so the requested integer BDF size renders one grid cell per pixel.
        # Outlines and metrics remain in their original units; source bytes stay
        # untouched. This is an explicit, reviewed override, never auto-detection.
        from io import BytesIO
        from fontTools.ttLib import TTFont

        if (not isinstance(grid_units, int) or isinstance(grid_units, bool)
                or grid_units <= 0 or not 16 <= ppem * grid_units <= 16384):
            raise ValueError(f"{path}: invalid grid_units: {grid_units}")
        if hinting:
            raise ValueError(f"{path}: explicit grid_units requires hinting off")
        with TTFont(path) as font:
            font["head"].unitsPerEm = ppem * grid_units
            font.flavor = None
            stream = BytesIO()
            font.save(stream)
        face = freetype.Face.from_bytes(stream.getvalue())
    else:
        face = freetype.Face(str(_materialize_sfnt(path)))
    if axes:
        info = face.get_variation_info()
        unknown = axes.keys() - {a.tag for a in info.axes}
        if unknown:
            raise ValueError(f"{path}: unknown variation axes: {sorted(unknown)}")
        coords = []
        for axis in info.axes:
            value = axes.get(axis.tag, axis.default)
            if not axis.minimum <= value <= axis.maximum:
                raise ValueError(f"{path}: {axis.tag}={value} is outside its axis range")
            coords.append(value)
        face.set_var_design_coords(coords)
    face.set_pixel_sizes(0, ppem)
    # Hinting off by default. Nearly every font here is already drawn on the
    # pixel grid, and on those the hinter re-snaps stems that are exactly where
    # they belong -- 1px strokes come back 2px, counters fill in.
    #
    # Off-grid outlines need individual review. DotGothic16 needs a subpixel
    # translation before unhinted rasterization: its shipped hinting distorts
    # kana strokes, while unshifted outlines double strokes. The explicit
    # pixel_offset preserves the reviewed grid without changing other fonts.
    flags = freetype.FT_LOAD_RENDER | freetype.FT_LOAD_MONOCHROME | freetype.FT_LOAD_TARGET_MONO
    if not hinting:
        flags |= freetype.FT_LOAD_NO_HINTING

    glyphs: dict[int, Glyph] = {}
    unencoded: list[Glyph] = []
    warnings: list[str] = []
    names: list[str] = []
    if all_glyphs:
        from fontTools.ttLib import TTFont

        with TTFont(path) as font:
            names = font.getGlyphOrder()
    if glyph_offsets:
        unknown = glyph_offsets.keys() - set(names)
        if unknown:
            raise ValueError(f"{path}: unknown glyph offsets: {sorted(unknown)}")
    used_indices: set[int] = set()

    def render(index: int, cp: int, name: str) -> Glyph:
        if glyph_offsets or pixel_offset is not None:
            # Standalone dot components may be centred on the origin, whereas
            # their occurrences in text are translated to pixel centres. Use
            # the explicitly reviewed pixel offset for those component glyphs.
            dx, dy = (glyph_offsets or {}).get(name, (0, 0))
            face.set_transform(
                freetype.Matrix(0x10000, 0, 0, 0x10000),
                freetype.Vector(round((dx + origin[0]) * 64), round((dy + origin[1]) * 64)),
            )
        face.load_glyph(index, flags)
        bm = face.glyph.bitmap
        w, h = bm.width, bm.rows
        nb = row_bytes(w)
        rows = bytearray()
        for y in range(h):
            row = bytes(bm.buffer[y * bm.pitch : y * bm.pitch + nb])
            rows += row.ljust(nb, b"\x00")[:nb]
        return Glyph(
            # Unhinted advances are 26.6 fixed-point values. Truncating 8.97px
            # to 8 loses a whole spacing pixel in fonts such as Chunky Sans 11.
            cp=cp, name=name, dwidth=round(face.glyph.advance.x / 64),
            bbw=w, bbh=h, bbx=face.glyph.bitmap_left,
            bby=face.glyph.bitmap_top - h, rows=bytes(rows),
        )

    cp, gindex = face.get_first_char()
    while gindex:
        if cp not in glyphs and (all_glyphs or cp >= 0x20):
            try:
                # Keep original names, adding a suffix only for cmap aliases of
                # a glyph already represented under another Unicode character.
                name = names[gindex] if names else f"uni{cp:04X}"
                if names and gindex in used_indices:
                    name += f".U{cp:04X}"
                glyphs[cp] = render(gindex, cp, name)
                used_indices.add(gindex)
            except Exception as e:  # noqa: BLE001 - a single glyph failure only warns
                if all_glyphs:
                    raise ValueError(f"{path}: failed to retain U+{cp:04X}") from e
                warnings.append(f"U+{cp:04X}: {e}")
        cp, gindex = face.get_next_char(cp, gindex)

    if all_glyphs:
        for index, name in enumerate(names):
            if index not in used_indices:
                # ENCODING -1 retains alternate/ligature/component glyphs in
                # the BDF without assigning fabricated Unicode or PUA values.
                unencoded.append(render(index, -1, name))

    if not glyphs:
        raise ValueError(f"{path}: rasterization produced no glyphs")

    asc = face.size.ascender >> 6
    desc = -(face.size.descender >> 6)
    rendered = [*glyphs.values(), *unencoded]
    max_top = max(g.bby + g.bbh for g in rendered)
    max_bottom = max(-g.bby for g in rendered)
    if asc + desc > ppem * 1.6:
        asc, desc = max_top, max(max_bottom, 0)
        warnings.append("ascender/descender implausible, measured from the glyphs instead")

    xoff = min(g.bbx for g in rendered)
    yoff = min(g.bby for g in rendered)
    bw = max(g.bbx + g.bbw for g in rendered) - xoff
    bh = max(g.bby + g.bbh for g in rendered) - yoff
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
        unencoded_glyphs=unencoded,
    )
