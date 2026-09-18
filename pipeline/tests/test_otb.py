from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import E_B_D_T_, E_B_L_C_
from fontTools.ttLib.tables.BitmapGlyphMetrics import BigGlyphMetrics

from opf.ingest.otb import convert_otb
from opf.model import Glyph, ParsedFont
from opf.ttfexport import build_ttf


def test_format_five_shared_metrics_aliases_and_unencoded_glyphs(tmp_path):
    path = tmp_path / 'shared.otb'
    glyphs = [Glyph(cp, f'uni{cp:04X}', 4, 3, 2, -1, -1, b'\xa0\x40') for cp in [65, 66]]
    bitmap = ParsedFont(Path('fixture.bdf'), 'fixture', 'fixture.bdf', {}, 4, 3, 1,
                        (3, 2, -1, -1), glyphs)
    build_ttf([bitmap], 'Test', 'Regular', path)
    font = TTFont(path)
    names = list(font['EBDT'].strikeData[0])
    # One cmap alias and a second bitmap reachable only by its glyph index.
    for cmap in font['cmap'].tables:
        cmap.cmap = {65: names[0], 0x391: names[0]}
    metrics = BigGlyphMetrics()
    for key, value in {'width': 3, 'height': 2, 'horiBearingX': -1, 'horiBearingY': 1,
                       'horiAdvance': 4, 'vertBearingX': 0, 'vertBearingY': 0,
                       'vertAdvance': 4}.items():
        setattr(metrics, key, value)
    subtable = E_B_L_C_.eblc_index_sub_table_2(b'', font)
    subtable.indexFormat = 2
    subtable.imageFormat = 5
    subtable.imageDataOffset = 0
    subtable.imageSize = 1
    subtable.metrics = metrics
    subtable.names = names
    font['EBLC'].strikes[0].indexSubTables = [subtable]
    data = {}
    for name in names:
        glyph = E_B_D_T_.ebdt_bitmap_format_5(b'', font)
        glyph.imageData = b'\xa8'  # continuous bits: row 101, then row 010
        data[name] = glyph
    font['EBDT'].strikeData = [data]
    font.save(path)

    complete = convert_otb(path, 'fixture', all_glyphs=True)[0][1]
    assert [g.cp for g in complete.glyphs] == [65, 0x391]
    assert len(complete.unencoded_glyphs) == 1
    for glyph in complete.glyphs + complete.unencoded_glyphs:
        assert (glyph.bbw, glyph.bbh, glyph.bbx, glyph.bby, glyph.dwidth) == (3, 2, -1, -1, 4)
        assert glyph.rows == b'\xa0\x40'
    assert not convert_otb(path, 'fixture')[0][1].unencoded_glyphs
