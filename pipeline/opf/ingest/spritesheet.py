"""Decode explicitly mapped pixel sheets without scaling or guessing Unicode."""

from pathlib import Path
import re

from PIL import Image

from opf.model import Glyph, ParsedFont, row_bytes


def convert_spritesheet(path: Path, family_slug: str, spec: dict) -> ParsedFont:
    """Cells use top-left image coordinates; baseline is measured from cell top.

    A regular sheet supplies cell_size and characters (one character per cell).
    Irregular sheets supply cells with rect, char (or name for unencoded glyphs),
    and optional advance/baseline. Foreground is either an explicit RGB palette
    or nontransparent pixels. Unmapped visible cells are rejected, not dropped.
    """
    with Image.open(path) as source:
        image = source.convert("RGBA")
    size = int(spec["pixel_size"])
    baseline = int(spec.get("baseline", size))
    palette = {tuple(c) for c in spec.get("foreground", [])}

    def lit(pixel):
        return pixel[3] > 0 and (not palette or pixel[:3] in palette)

    cells = spec.get("cells")
    if cells is None:
        width, height = spec["cell_size"]
        if image.width % width:
            raise ValueError(f"{path}: sheet width is not a multiple of cell width")
        columns = image.width // width
        chars = spec["characters"]
        cells = []
        for i in range(columns * (image.height // height)):
            x, y = i % columns * width, i // columns * height
            char = chars[i] if i < len(chars) else ""
            if not char:
                if any(lit(image.getpixel((x + px, y + py)))
                       for py in range(height) for px in range(width)):
                    raise ValueError(f"{path}: visible cell {i} has no character mapping")
                continue
            cells.append({"char": char, "rect": [x, y, width, height]})
        if len(chars) > columns * (image.height // height):
            raise ValueError(f"{path}: character map extends beyond the sheet")
    glyphs, unencoded = [], []
    seen = set()
    for i, cell in enumerate(cells):
        x, y, width, height = cell["rect"]
        if min(x, y, width, height) < 0 or x + width > image.width or y + height > image.height:
            raise ValueError(f"{path}: cell {i} is outside the sheet")
        char = cell.get("char", "")
        if len(char) > 1:
            raise ValueError(f"{path}: cell {i} must map to one Unicode scalar")
        cp = ord(char) if char else -1
        pixels = image.crop((x, y, x + width, y + height))
        stride = row_bytes(width)
        rows = bytearray(stride * height)
        for py in range(height):
            for px in range(width):
                if lit(pixels.getpixel((px, py))):
                    rows[py * stride + px // 8] |= 128 >> (px % 8)
        if spec.get("omit_blank", False) and not any(rows) and not char.isspace():
            continue
        if cp >= 0:
            if cp in seen:
                raise ValueError(f"{path}: duplicate mapping U+{cp:04X}")
            seen.add(cp)
        glyph = Glyph(cp, cell.get("name", f"uni{cp:04X}" if cp >= 0 else f"cell{i}"),
                      int(cell.get("advance", width)), width, height,
                      int(cell.get("bearing_x", 0)), int(cell.get("baseline", baseline)) - height,
                      bytes(rows))
        (glyphs if cp >= 0 else unencoded).append(glyph)
    all_glyphs = glyphs + unencoded
    if not all_glyphs:
        raise ValueError(f"{path}: no glyphs")
    left = min(g.bbx for g in all_glyphs)
    bottom = min(g.bby for g in all_glyphs)
    top = max(g.bby + g.bbh for g in all_glyphs)
    right = max(g.bbx + g.bbw for g in all_glyphs)
    name = spec.get("name", family_slug)
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError(f"{path}: invalid variant name")
    return ParsedFont(path, family_slug, f"{name}-{size}px.bdf",
                      {"PIXEL_SIZE": size, "CHARSET_REGISTRY": "ISO10646", "CHARSET_ENCODING": "1"},
                      size, max(top, 0), max(-bottom, 0), (right-left, top-bottom, left, bottom),
                      sorted(glyphs, key=lambda g: g.cp), unencoded_glyphs=unencoded)
