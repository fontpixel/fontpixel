import gzip
import hashlib
import json

import pytest

from opf.coverage.charsets import DATA_DIR, load_charsets
from opf.coverage.cjk import cjk_coverage, cjk_sets, refresh_cjk_details
from opf.coverage.ucd import load_ucd


@pytest.fixture(scope='module')
def references():
    charsets = load_charsets()
    ucd = load_ucd(DATA_DIR / 'ucd')
    return charsets, ucd, cjk_sets(charsets, ucd)


def test_reference_sets_are_exact_and_compatibility_is_separate(references):
    charsets, _, sets = references
    assert len(sets['han']) == 101996
    assert sets['union'] <= sets['han']
    assert len(sets['tw']) == 11151
    assert len(sets['kr']) == 4620
    assert len(sets['kr-compat']) == 268
    assert not sets['kr'] & sets['kr-compat']
    assert sets['kr'] | sets['kr-compat'] == next(c.cps for c in charsets if c.id == 'ksx1001-hanja')
    assert sets['union'] == sets['tw'] | sets['sc'] | sets['jp'] | sets['kr']
    assert len(sets['union']) == 14818
    assert sets['kana'] == sets['hiragana'] | sets['katakana'] | sets['kana-ext'] | sets['kana-halfwidth']
    assert len(sets['hiragana']) == 93
    assert len(sets['jamo']) == 451
    assert sets['combined'] == sets['union'] | sets['kana'] | sets['hangul'] | sets['bopomofo']
    assert len(sets['combined']) == 26644
    assert not sets['combined'] & sets['jamo']
    assert not sets['combined'] & sets['kr-compat']


def test_intersections_count_glyphs_instead_of_combining_coverage_totals(references):
    _, _, sets = references
    shared = min(sets['tw-sc'])
    exclusive = min(sets['jp-only'])
    compat = min(sets['kr-compat'])
    cps = frozenset([shared, exclusive, compat, 0x41, 0x0378])
    result = cjk_coverage(cps, sets)
    assert result['union'] == [2, 14818]
    assert result['tw-sc'] == [1, 4899]
    assert result['jp-only'] == [1, 201]
    assert result['kr-compat'] == [1, 268]
    assert result['han'] == [2, 101996]
    assert all(0 <= have <= total for have, total in result.values())
    assert all(have == 0 for have, _ in cjk_coverage(frozenset([0x41]), sets).values())
    assert all(have == total for have, total in cjk_coverage(frozenset().union(*sets.values()), sets).values())


def test_combined_summary_includes_non_han_scripts_without_double_counting(references):
    _, _, sets = references
    cps = frozenset([min(sets['tw-sc']), 0x3042, 0xAC00, 0x3105, 0x1100, 0xF900])
    result = cjk_coverage(cps, sets)
    assert result['union'] == [1, 14818]
    assert result['combined'] == [4, 26644]
    assert result['jamo'][0] == 1
    assert result['kr-compat'][0] == 1


def test_cached_details_refresh_per_variant_when_bdf_changes(tmp_path, references):
    charsets, ucd, _ = references
    (tmp_path / 'details').mkdir()
    detail_path = tmp_path / 'details' / 'test.json'
    entries = [{'slug': 'test', 'variants': [{'id': 'a'}, {'id': 'b'}]}]

    def bdf(variant, cp):
        data = gzip.compress(f'ENCODING {cp}\nENCODING -1\n'.encode())
        filename = f'{variant}.bdf.gz'
        (tmp_path / filename).write_bytes(data)
        return {'kind': 'bdf', 'variantId': variant, 'file': filename,
                'sha256': hashlib.sha256(data).hexdigest()}

    detail_path.write_text(json.dumps({'downloads': [bdf('a', 0x41), bdf('b', 0x4E00)]}))
    refresh_cjk_details(entries, tmp_path, tmp_path, charsets, ucd)
    detail = json.loads(detail_path.read_text())
    assert detail['cjkCoverage']['a']['han'][0] == 0
    assert detail['cjkCoverage']['b']['han'][0] == 1
    modified = detail_path.stat().st_mtime_ns
    refresh_cjk_details(entries, tmp_path, tmp_path, charsets, ucd)
    assert detail_path.stat().st_mtime_ns == modified
    detail['downloads'][0] = bdf('a', 0x4E00)
    detail_path.write_text(json.dumps(detail))
    refresh_cjk_details(entries, tmp_path, tmp_path, charsets, ucd)
    assert json.loads(detail_path.read_text())['cjkCoverage']['a']['han'][0] == 1
