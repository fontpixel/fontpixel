import gzip
import hashlib
import json

import pytest

from opf.coverage.charsets import DATA_DIR, load_charsets
from opf.coverage.cjk import cjk_coverage, cjk_sets, refresh_cjk_details
from opf.coverage.engine import overview
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
    assert len(sets['union']) == 14901
    assert sets['kana'] == sets['hiragana'] | sets['katakana'] | sets['kana-marks'] | sets['kana-ext'] | sets['kana-halfwidth']
    assert len(sets['hiragana']) == 86
    assert len(sets['katakana']) == 90
    assert len(sets['kana-marks']) == 13
    assert len(sets['jp']) == 2965
    assert sets['jp'] == next(c.cps for c in charsets if c.id == 'jisx0208-l1')
    assert len(sets['jamo']) == 451
    assert sets['combined'] == sets['union'] | sets['kana'] | sets['hangul'] | sets['bopomofo']
    assert len(sets['combined']) == 26727
    assert not sets['combined'] & sets['jamo']
    assert not sets['combined'] & sets['kr-compat']


def test_intersections_count_glyphs_instead_of_combining_coverage_totals(references):
    _, _, sets = references
    shared = min(sets['tw-sc'])
    exclusive = min(sets['jp-only'])
    compat = min(sets['kr-compat'])
    cps = frozenset([shared, exclusive, compat, 0x41, 0x0378])
    result = cjk_coverage(cps, sets)
    assert result['union'] == [2, 14901]
    assert result['tw-sc'] == [1, 4899]
    assert result['jp-only'] == [1, 284]
    assert result['kr-compat'] == [1, 268]
    assert result['han'] == [2, 101996]
    assert all(0 <= have <= total for have, total in result.values())
    assert all(have == 0 for have, _ in cjk_coverage(frozenset([0x41]), sets).values())
    assert all(have == total for have, total in cjk_coverage(frozenset().union(*sets.values()), sets).values())


def test_combined_summary_includes_non_han_scripts_without_double_counting(references):
    _, _, sets = references
    cps = frozenset([min(sets['tw-sc']), 0x3042, 0xAC00, 0x3105, 0x1100, 0xF900])
    result = cjk_coverage(cps, sets)
    assert result['union'] == [1, 14901]
    assert result['combined'] == [4, 26727]
    assert result['jamo'][0] == 1
    assert result['kr-compat'][0] == 1


def test_han_unions_and_multiway_intersections_count_each_code_point_once(references):
    _, _, sets = references
    # One character shared by all four tables, one exclusive to each of Japan
    # and Korea, plus compatibility Han and Latin outside these reference sets.
    cps = frozenset([0x4E00, min(sets['jp-only']), min(sets['kr-only']), 0xF900, 0x41])
    result = cjk_coverage(cps, sets)
    expected = {
        'tw-sc-union': [1, 14357],
        'tw-sc-jp-union': [2, 14694],
        'tw-sc-kr-union': [2, 14617],
        'tw-sc-jp': [1, 1771],
        'tw-sc-kr': [1, 2733],
        'tw-sc-jp-kr': [1, 1698],
    }
    assert {key: result[key] for key in expected} == expected
    assert sets['tw-sc-jp-kr'] <= sets['tw-sc-jp'] <= sets['tw-sc']
    assert sets['tw-sc-jp-kr'] <= sets['tw-sc-kr'] <= sets['tw-sc']
    assert 'kr-sc-not-tw' not in result


def test_map_and_coverage_tables_share_letter_and_han_definitions(references):
    charsets, ucd, sets = references
    c = {c.id: c.cps for c in charsets}
    for key in ('hiragana', 'katakana', 'bopomofo'):
        assert sets[key] == c[key]
    parts = [sets[k] for k in ('hiragana', 'katakana', 'kana-marks', 'kana-ext', 'kana-halfwidth')]
    assert len(sets['kana']) == sum(map(len, parts)) == 579
    assert sets['jamo'] == c['hangul-jamo'] | c['hangul-compat-jamo'] | sets['jamo-ext']
    assert len(sets['jamo-ext']) == 101
    cps = frozenset({0xFA0E, 0xF900, 0x4E00, 0x4DBF, 0x0378})
    assert list(overview(cps, ucd)['han_total']) == cjk_coverage(cps, sets)['han']


def test_exclusive_han_are_absent_from_all_other_three_sets(references):
    _, _, sets = references
    totals = {'tw': 4638, 'sc': 3028, 'jp': 284, 'kr': 207}
    cps = frozenset([0x4E00, *(min(sets[f'{key}-only']) for key in totals)])
    result = cjk_coverage(cps, sets)
    for key, total in totals.items():
        exclusive = sets[f'{key}-only']
        assert exclusive <= sets[key]
        assert all(not exclusive & sets[other] for other in totals if other != key)
        assert result[f'{key}-only'] == [1, total]


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

    detail_path.write_text(json.dumps({
        'downloads': [bdf('a', 0xFA0E), bdf('b', 0xF900)],
        'overview': {'a': {'hanTotal': [0, 101984], 'compat': [1, 1026]}, 'b': {}},
        'cjkCoverage': {'a': {'kr-sc-not-tw': [0, 66]}},
    }))
    refresh_cjk_details(entries, tmp_path, tmp_path, charsets, ucd)
    detail = json.loads(detail_path.read_text())
    assert detail['cjkCoverage']['a']['han'][0] == 1
    assert detail['cjkCoverage']['b']['han'][0] == 0
    assert 'kr-sc-not-tw' not in detail['cjkCoverage']['a']
    assert detail['cjkCoverage']['a']['tw-sc-jp-kr'][1] == 1698
    assert detail['overview']['a']['hanTotal'] == [1, 101996]
    assert detail['overview']['a']['compat'][0] == 0
    assert detail['overview']['b']['compat'][0] == 1
    assert len(detail['missingChars']['a']['kana-marks']) == 13
    assert len(detail['missingChars']['a']['jamo']) == 451
    assert len(detail['missingChars']['a']['kr-compat']) == 268
    assert 'han' not in detail['missingChars']['a']  # Large absent sets are not embedded.
    modified = detail_path.stat().st_mtime_ns
    refresh_cjk_details(entries, tmp_path, tmp_path, charsets, ucd)
    assert detail_path.stat().st_mtime_ns == modified
    detail['downloads'][0] = bdf('a', 0x3042)
    detail_path.write_text(json.dumps(detail))
    refresh_cjk_details(entries, tmp_path, tmp_path, charsets, ucd)
    assert json.loads(detail_path.read_text())['cjkCoverage']['a']['hiragana'][0] == 1
