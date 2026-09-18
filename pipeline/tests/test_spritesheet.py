import pytest
from pathlib import Path
from PIL import Image

from opf.ingest.spritesheet import convert_spritesheet
from opf.ingest.bdfwrite import write_bdf
from opf.parsers.bdf import parse_bdf
from opf.model import row_bytes


def _counters(glyph):
    """Count enclosed blank regions, independently of the foreground palette."""
    stride = row_bytes(glyph.bbw)
    blank = {(x, y) for y in range(glyph.bbh) for x in range(glyph.bbw)
             if not glyph.rows[y * stride + x // 8] & (128 >> (x % 8))}
    count = 0
    while blank:
        pending = [blank.pop()]
        region = set(pending)
        while pending:
            x, y = pending.pop()
            for point in [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]:
                if point in blank:
                    blank.remove(point)
                    region.add(point)
                    pending.append(point)
        if all(0 < x < glyph.bbw - 1 and 0 < y < glyph.bbh - 1 for x, y in region):
            count += 1
    return count


@pytest.mark.parametrize('name', [
    'numbers-gold-11px', 'numbers-gold-large-18px',
    'numbers-red-large-18px', 'numbers-scrolling-9px',
])
def test_frogatto_digit_counters_are_not_filled_by_coloured_backgrounds(name):
    path = Path(__file__).resolve().parents[2] / 'fonts/frogatto-numbers' / f'{name}.bdf'
    font = parse_bdf(path, 'frogatto-numbers')
    glyphs = {g.cp: g for g in font.glyphs}
    for char, expected in [('0', 1), ('6', 1), ('8', 2), ('9', 1)]:
        assert _counters(glyphs[ord(char)]) == expected


def test_preserves_bits_mapping_palette_and_baseline(tmp_path):
    image = Image.new("RGBA", (18, 3), (10, 20, 30, 255))
    for x, y in [(0, 0), (8, 2), (9, 1)]:
        image.putpixel((x, y), (255, 255, 255, 255))
    path = tmp_path / "sheet.png"
    image.save(path)
    font = convert_spritesheet(path, "sample", {
        "pixel_size": 3, "baseline": 2, "cell_size": [9, 3],
        "characters": "AЖ", "foreground": [[255, 255, 255]],
    })
    assert [g.cp for g in font.glyphs] == [65, 0x416]
    assert font.glyphs[0].rows == b"\x80\x00\x00\x00\x00\x80"
    assert font.glyphs[0].bby == -1
    assert font.glyphs[1].rows == b"\x00\x00\x80\x00\x00\x00"
    out = tmp_path / "out.bdf"
    write_bdf(font, out)
    assert parse_bdf(out, "sample").glyphs == font.glyphs


def test_rejects_visible_unmapped_cell_and_duplicate_unicode(tmp_path):
    image = Image.new("RGBA", (2, 1), "white")
    path = tmp_path / "sheet.png"
    image.save(path)
    spec = {"pixel_size": 1, "cell_size": [1, 1], "characters": "A"}
    with pytest.raises(ValueError, match="no character mapping"):
        convert_spritesheet(path, "sample", spec)
    with pytest.raises(ValueError, match="duplicate mapping"):
        convert_spritesheet(path, "sample", {**spec, "characters": "AA"})


def test_unencoded_cells_and_blank_space_are_retained(tmp_path):
    image = Image.new("RGBA", (3, 1))
    image.putpixel((2, 0), (255, 255, 255, 255))
    path = tmp_path / "sheet.png"
    image.save(path)
    font = convert_spritesheet(path, "sample", {
        "pixel_size": 1, "omit_blank": True,
        "cells": [{"rect": [0, 0, 1, 1], "char": " "},
                  {"rect": [1, 0, 1, 1], "char": "A"},
                  {"rect": [2, 0, 1, 1], "name": "ornament"}],
    })
    assert [g.cp for g in font.glyphs] == [32]
    assert font.unencoded_glyphs[0].name == "ornament"
    assert font.unencoded_glyphs[0].rows == b"\x80"
