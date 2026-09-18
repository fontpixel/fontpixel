from pathlib import Path
import hashlib
import json

import pytest
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib.tables.TupleVariation import TupleVariation

from opf.ingest.bdfwrite import write_bdf
from opf.ingest.rasterize import rasterize_ttf
from opf.ingest.run import run_manifest
from opf.parsers.bdf import parse_bdf


@pytest.fixture
def source(tmp_path):
    """A tiny variable font with a supplementary-plane alias and an alternate."""
    order = ['.notdef', 'return', 'A', 'A.alt', 'Omega', 'dot']
    glyphs = {}
    for name in order:
        pen = TTGlyphPen(None)
        if name == 'dot':
            pen.moveTo((0, -50))
            pen.qCurveTo((-50, -50), (-50, 0))
            pen.qCurveTo((-50, 50), (0, 50))
            pen.qCurveTo((50, 50), (50, 0))
            pen.qCurveTo((50, -50), (0, -50))
            pen.closePath()
        elif name != 'return':
            pen.moveTo((0, 0))
            pen.lineTo((100, 0))
            pen.lineTo((100, 500))
            pen.lineTo((0, 500))
            pen.closePath()
        glyphs[name] = pen.glyph()
    fb = FontBuilder(1000, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap({13: 'return', 65: 'A', 0x3A9: 'Omega', 0x10400: 'A'})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics({name: (600, -50 if name == 'dot' else 0) for name in order})
    fb.setupHorizontalHeader(ascent=800, descent=-200)
    fb.setupNameTable({'familyName': 'Complete Test', 'styleName': 'Regular'})
    fb.setupOS2(sTypoAscender=800, sTypoDescender=-200, usWinAscent=800, usWinDescent=200)
    fb.setupPost()
    fb.setupFvar([('wght', 400, 400, 700, 'Weight')], [])
    deltas = [(0, 0), (100, 0), (100, 0), (0, 0)] + [(0, 0)] * 4
    fb.setupGvar({'A': [TupleVariation({'wght': (0, 1, 1)}, deltas)]})
    path = tmp_path / 'source.ttf'
    fb.save(path)
    return path


def test_complete_bdf_preserves_cmap_aliases_controls_and_unencoded_glyphs(source, tmp_path):
    raster = rasterize_ttf(source, 10, 'complete', all_glyphs=True)
    assert [g.cp for g in raster.glyphs] == [13, 65, 0x3A9, 0x10400]
    assert [g.name for g in raster.unencoded_glyphs] == ['.notdef', 'A.alt', 'dot']
    glyphs = [*raster.glyphs, *raster.unencoded_glyphs]
    assert len({g.name for g in glyphs}) == len(glyphs)
    bdf = tmp_path / 'complete.bdf'
    write_bdf(raster, bdf)
    assert 'CHARS 7\n' in bdf.read_text()
    assert bdf.read_text().count('ENCODING -1\n') == 3
    parsed = parse_bdf(bdf, 'complete')
    assert parsed.glyphs == raster.glyphs
    assert parsed.unencoded_glyphs == raster.unencoded_glyphs
    assert not parsed.warnings


def test_existing_conversion_keeps_its_original_control_and_alternate_policy(source):
    raster = rasterize_ttf(source, 10, 'legacy')
    assert [g.cp for g in raster.glyphs] == [65, 0x3A9, 0x10400]
    assert raster.unencoded_glyphs == []


def test_fractional_advances_round_to_the_nearest_bitmap_pixel(source):
    from fontTools.ttLib import TTFont

    # Tiny em/grid rounding errors must not discard the intended spacing pixel.
    with TTFont(source) as font:
        font['hmtx'].metrics['A'] = (699, 0)  # 6.99px at 10ppem
        font['hmtx'].metrics['Omega'] = (601, 0)  # 6.01px, not a blanket ceil
        font['hmtx'].metrics['dot'] = (0, -50)  # A combining glyph stays zero-width
        font.save(source)
    raster = rasterize_ttf(source, 10, 'advances', all_glyphs=True)
    by_cp = {g.cp: g for g in raster.glyphs}
    assert by_cp[65].dwidth == 7
    assert by_cp[0x3A9].dwidth == 6
    assert next(g for g in raster.unencoded_glyphs if g.name == 'dot').dwidth == 0


def test_named_variable_instances_reproduce_both_weights_and_full_coverage(source, tmp_path):
    manifest = tmp_path / 'manifest.toml'
    manifest.write_text('''[[family]]
slug = "complete"
source = "."
convert = "ttf"
convert_take = ["source.ttf"]
ppem = 10
all_glyphs = true
instances = [
  { name = "Complete-Regular", axes = { wght = 400 }, weight = "regular" },
  { name = "Complete-Bold", axes = { wght = 700 }, weight = "bold" },
]
''')
    dest = tmp_path / 'fonts'
    report = run_manifest(manifest, source.parent, dest)
    assert report.errors == []
    regular = parse_bdf(dest / 'complete/Complete-Regular-10px.bdf', 'complete')
    bold = parse_bdf(dest / 'complete/Complete-Bold-10px.bdf', 'complete')
    assert regular.props['WEIGHT_NAME'] == 'regular'
    assert bold.props['WEIGHT_NAME'] == 'bold'
    assert regular.glyphs[1].bbw == 1
    assert bold.glyphs[1].bbw == 2
    assert [g.cp for g in regular.glyphs] == [g.cp for g in bold.glyphs]
    assert len(regular.unencoded_glyphs) == len(bold.unencoded_glyphs) == 3
    again = run_manifest(manifest, source.parent, dest)
    assert again.errors == []
    assert again.skipped == ['complete']


def test_instances_can_be_pinned_separately_for_multiple_source_fonts(source, tmp_path):
    (source.parent / 'other.ttf').write_bytes(source.read_bytes())
    manifest = tmp_path / 'multiple.toml'
    manifest.write_text('''[[family]]
slug = "multiple"
source = "."
convert = "ttf"
convert_take = ["*.ttf"]
ppem = 10
all_glyphs = true
[family.instances]
"source.ttf" = [{ name = "First", axes = { wght = 400 } }]
"other.ttf" = [{ name = "Second", axes = { wght = 700 } }]
''')
    dest = tmp_path / 'fonts'
    report = run_manifest(manifest, source.parent, dest)
    assert not report.errors
    assert sorted(p.name for p in (dest / 'multiple').glob('*.bdf')) == ['First-10px.bdf', 'Second-10px.bdf']
    first = parse_bdf(dest / 'multiple/First-10px.bdf', 'multiple')
    second = parse_bdf(dest / 'multiple/Second-10px.bdf', 'multiple')
    assert first.glyphs[1].bbw == 1
    assert second.glyphs[1].bbw == 2


@pytest.mark.parametrize('axes', [{'wght': 999}, {'typo': 400}])
def test_invalid_axes_are_not_silently_ignored(source, axes):
    with pytest.raises(ValueError):
        rasterize_ttf(source, 10, 'complete', axes=axes)


def test_origin_centred_dot_can_be_restored_without_moving_text_glyphs(source):
    normal = rasterize_ttf(source, 10, 'dots', all_glyphs=True)
    assert not any(next(g for g in normal.unencoded_glyphs if g.name == 'dot').rows)
    aligned = rasterize_ttf(source, 10, 'dots', all_glyphs=True,
                            glyph_offsets={'dot': [0.5, 0.5]})
    assert normal.glyphs == aligned.glyphs
    dot = next(g for g in aligned.unencoded_glyphs if g.name == 'dot')
    assert (dot.bbw, dot.bbh, dot.rows) == (1, 1, b'\x80')


def test_global_pixel_offset_preserves_advances_and_combines_with_glyph_offsets(source, tmp_path):
    normal = rasterize_ttf(source, 10, 'offset', all_glyphs=True)
    shifted = rasterize_ttf(source, 10, 'offset', all_glyphs=True,
                            pixel_offset=[1, 2], glyph_offsets={'dot': [-0.5, -1.5]})
    for before, after in zip(normal.glyphs, shifted.glyphs):
        assert before.dwidth == after.dwidth
        if any(before.rows):
            assert before.rows == after.rows
            assert (after.bbx, after.bby) == (before.bbx + 1, before.bby + 2)
    dot = next(g for g in shifted.unencoded_glyphs if g.name == 'dot')
    assert (dot.bbw, dot.bbh, dot.rows) == (1, 1, b'\x80')

    manifest = tmp_path / 'offset.toml'
    manifest.write_text('''[[family]]
slug = "offset"
source = "."
convert = "ttf"
convert_take = ["source.ttf"]
ppem = 10
all_glyphs = true
pixel_offset = [1, 2]
glyph_offsets = { dot = [-0.5, -1.5] }
''')
    report = run_manifest(manifest, source.parent, tmp_path / 'fonts')
    assert not report.errors
    imported = parse_bdf(tmp_path / 'fonts/offset/source-10px.bdf', 'offset')
    assert imported.glyphs == shifted.glyphs
    assert imported.unencoded_glyphs == shifted.unencoded_glyphs


@pytest.mark.parametrize('offset', [[0], [0, 0, 0], [float('inf'), 0], [True, 0]])
def test_invalid_global_pixel_offsets_are_rejected(source, offset):
    with pytest.raises(ValueError, match='invalid pixel_offset'):
        rasterize_ttf(source, 10, 'offset', pixel_offset=offset)


def test_explicit_grid_preserves_pixels_when_em_is_not_a_multiple(source, tmp_path):
    original = source.read_bytes()
    native = rasterize_ttf(source, 10, 'grid', all_glyphs=True)
    normalized = rasterize_ttf(source, 11, 'grid', all_glyphs=True, grid_units=100)
    assert normalized.pixel_size == 11
    assert normalized.glyphs == native.glyphs
    assert normalized.unencoded_glyphs == native.unencoded_glyphs
    assert source.read_bytes() == original

    manifest = tmp_path / 'grid.toml'
    manifest.write_text('''[[family]]
slug = "grid"
source = "."
convert = "ttf"
convert_take = ["source.ttf"]
ppem = { "source.ttf" = 11 }
grid_units = { "source.ttf" = 100 }
all_glyphs = true
''')
    dest = tmp_path / 'fonts'
    report = run_manifest(manifest, source.parent, dest)
    assert not report.errors
    parsed = parse_bdf(dest / 'grid/source-11px.bdf', 'grid')
    assert parsed.glyphs == native.glyphs
    assert parsed.unencoded_glyphs == native.unencoded_glyphs


@pytest.mark.parametrize('grid', [0, -1, 100.5, True, 20000])
def test_invalid_explicit_grid_is_rejected(source, grid):
    with pytest.raises(ValueError, match='grid_units'):
        rasterize_ttf(source, 10, 'grid', grid_units=grid)


def test_explicit_grid_does_not_use_hinting(source):
    with pytest.raises(ValueError, match='hinting'):
        rasterize_ttf(source, 10, 'grid', hinting=True, grid_units=100)


@pytest.mark.parametrize('audit_file', [
    'google-fonts-import-audit-2026-09-17.json',
    'google-fonts-jacquard-jersey-handjet-audit-2026-09-17.json',
    'google-fonts-bitcount-prop-single-audit-2026-09-17.json',
    'bitcount-family-audit-2026-09-17.json',
    'dotgothic16-import-audit-2026-09-18.json',
])
def test_imported_google_fonts_retain_complete_official_character_sets(audit_file):
    root = Path(__file__).resolve().parents[2]
    audit = json.loads((root / 'docs' / 'audits' / audit_file).read_text())

    def digest(value):
        encoded = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        return hashlib.sha256(encoded).hexdigest()

    for expected in audit['variants']:
        family = expected.get('current_family', expected['family'])
        font = parse_bdf(root / 'fonts' / family / expected['file'], family)
        cmap = {g.cp: g.name.removesuffix(f'.U{g.cp:04X}') for g in font.glyphs}
        names = sorted(g.name for g in font.unencoded_glyphs)
        assert len(cmap) == expected['unicode_characters']
        assert digest(cmap) == expected['cmap_sha256'], expected['file']
        assert len(names) == expected['unencoded_glyphs']
        assert digest(names) == expected['unencoded_names_sha256'], expected['file']
        assert not font.warnings
        if 'pixel_geometry_sha256' in expected:
            geometry = {}
            for g in [*font.glyphs, *font.unencoded_glyphs]:
                stride = (g.bbw + 7) // 8
                geometry[g.name.removesuffix(f'.U{g.cp:04X}')] = sorted(
                    (g.bbx + x, g.bby + g.bbh - y - 1)
                    for y in range(g.bbh) for x in range(g.bbw)
                    if g.rows[y * stride + x // 8] & (128 >> (x % 8))
                )
            # This fingerprint comes from an independent outline/component-grid
            # comparison, including every unencoded contextual glyph.
            assert digest(geometry) == expected['pixel_geometry_sha256'], expected['file']
