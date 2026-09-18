from pathlib import Path

import pytest

from opf.ingest.bdfwrite import write_bdf
from opf.ingest.header8x8 import convert_font8x8, convert_tmat
from opf.ingest.run import run_manifest
from opf.parsers.bdf import parse_bdf


def test_tmat_keeps_msb_pixels_and_roundtrips_all_ascii_slots(tmp_path):
    # Include literal braces in comments, as the real header does for { and }.
    cells = []
    for cp in range(32, 128):
        values = [2, 4, 8, 16, 32, 64, 128, 0] if cp == 47 else [0] * 8
        body = ''.join(f'    0b{v:08b},\n' for v in values)
        cells.append(f"{{ // {cp} (0x{cp:02x}) : '{chr(cp)}'\n{body}}},\n")
    source = tmp_path / 'arcade.h'
    source.write_text('static const unsigned char chars[][8] = {\n' + ''.join(cells) + '};')
    font = convert_tmat(source, 'arcade')
    write_bdf(font, tmp_path / 'arcade.bdf')
    parsed = parse_bdf(tmp_path / 'arcade.bdf', 'arcade')
    assert [g.cp for g in parsed.glyphs] == list(range(32, 128))
    slash = next(g for g in parsed.glyphs if g.cp == 47)
    assert slash.rows == bytes([2, 4, 8, 16, 32, 64, 128, 0])
    assert (slash.dwidth, slash.bbw, slash.bbh, slash.bbx, slash.bby) == (8, 8, 8, 0, -1)
    source.write_text('static const unsigned char chars[][8] = {};')
    with pytest.raises(ValueError, match='96 entries'):
        convert_tmat(source, 'arcade')


def test_font8x8_reverses_lsb_rows_and_uses_index_not_mistyped_comments(tmp_path):
    (tmp_path / 'font8x8.h').write_text('#include "font8x8_greek.h"\n#include "font8x8_misc.h"')
    (tmp_path / 'font8x8_greek.h').write_text('''
// unicode points U+03AA - U+03AB
char font8x8_greek[2][8] = {
 { 0x01, 0x03, 0x07, 0x0F, 0x1F, 0x3F, 0x7F, 0xFF}, // U+0399 (wrong upstream comment)
 { 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x00}, // U+03A5 (wrong upstream comment)
};''')
    (tmp_path / 'font8x8_misc.h').write_text('''
char font8x8_misc[2][8] = {
 { 0x01, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00}, // U+20A7
 { 0x01, 0x02, 0x03, 0x04, 0x00, 0x00, 0x00, 0x00}, // U+ (no mapping)
};''')
    f = convert_font8x8(tmp_path / 'font8x8.h', 'font8x8')
    assert [g.cp for g in f.glyphs] == [0x3AA, 0x3AB, 0x20A7]
    assert f.glyphs[0].rows == bytes([128, 192, 224, 240, 248, 252, 254, 255])
    assert f.glyphs[1].rows == bytes([64, 32, 16, 8, 4, 2, 1, 0])
    assert len(f.warnings) == 1
    assert 'no upstream Unicode mapping' in f.warnings[0]


def test_header_import_can_be_repeated_and_preserves_explicit_added_date(tmp_path):
    source = tmp_path / 'src'
    source.mkdir()
    (source / 'font8x8.h').write_text('''
// unicode points U+0041 - U+0041
char font8x8_basic[1][8] = {
 { 0x0C, 0x1E, 0x33, 0x33, 0x3F, 0x33, 0x33, 0x00}, // U+0041
};''')
    manifest = tmp_path / 'manifest.toml'
    manifest.write_text('''[[family]]
slug = "font8x8"
source = "."
convert = "font8x8"
convert_take = ["font8x8.h"]
added = "2026-09-17"
''')
    dest = tmp_path / 'fonts'
    first = run_manifest(manifest, source, dest)
    assert not first.errors
    assert first.imported == ['font8x8']
    bdf = dest / 'font8x8/font8x8-8px.bdf'
    original = bdf.read_bytes()
    second = run_manifest(manifest, source, dest)
    assert not second.errors
    assert second.skipped == ['font8x8']
    assert bdf.read_bytes() == original
    assert 'added = "2026-09-17"' in (dest / 'font8x8/family.toml').read_text()


def test_committed_fonts_keep_the_imported_writing_systems():
    root = Path(__file__).resolve().parents[2] / 'fonts'
    press = parse_bdf(root / 'press-start-2p/PressStart2P-Regular-8px.bdf', 'press-start-2p')
    cps = {g.cp for g in press.glyphs}
    assert len(cps) == 654
    assert all(ord(c) in cps for c in 'Αλφάβητο Ελληνικά Кириллица Ёё Її Āā Łł Œœ')
    assert sum(0x370 <= cp <= 0x3FF for cp in cps) == 74
    assert sum(0x400 <= cp <= 0x52F for cp in cps) == 184
    font8 = parse_bdf(root / 'font8x8/font8x8-8px.bdf', 'font8x8')
    cps8 = {g.cp for g in font8.glyphs}
    assert len(cps8) == 599
    assert {0x41, 0x192, 0x3AA, 0x3AB, 0x20A7, 0x2310, 0x2500, 0x2588, 0x3042, 0xE541} <= cps8
