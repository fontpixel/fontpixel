"""Exact code-point sets for the CJK relationship diagram.

The supplied Euler drawing is schematic, not area-proportional. Its approximate
totals are replaced with the site's reference tables and Unicode 17 assigned
characters. Compatibility ideographs are counted separately, never normalized:
a glyph at one code point does not imply coverage of another.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
from pathlib import Path

from opf.coverage.charsets import Charset
from opf.coverage.engine import UNIFIED_IN_COMPAT, _UNIFIED_RANGES
from opf.coverage.ucd import Ucd


def cjk_sets(charsets: list[Charset], ucd: Ucd) -> dict[str, frozenset[int]]:
    c = {item.id: item.cps for item in charsets}

    def blocks(*names: str) -> frozenset[int]:
        return frozenset(cp for name, a, b in ucd.blocks if name in names
                         for cp in range(a, b + 1) if cp in ucd.assigned)

    han = frozenset(cp for a, b in _UNIFIED_RANGES for cp in range(a, b + 1)
                    if cp in ucd.assigned) | UNIFIED_IN_COMPAT
    tw = c['tw-changyong-4808'] | c['tw-cichangyong-6343']
    sc, jp = c['tongyong-guifan'], c['joyo']
    kr = c['ksx1001-hanja'] & han
    hira, kata = blocks('Hiragana'), blocks('Katakana')
    kana_ext = blocks('Katakana Phonetic Extensions', 'Kana Supplement',
                      'Kana Extended-A', 'Kana Extended-B', 'Small Kana Extension')
    union = tw | sc | jp | kr
    kana = hira | kata | kana_ext | c['halfwidth-kana']
    bopomofo = blocks('Bopomofo', 'Bopomofo Extended')
    return {
        'han': han, 'union': union,
        # The overview combines the four Han tables and the three script
        # panels. Jamo and compatibility Han remain separate detail rows.
        'combined': union | kana | c['hangul-syllables'] | bopomofo,
        'tw': tw, 'tw-common': c['tw-changyong-4808'],
        'tw-less': c['tw-cichangyong-6343'],
        'sc': sc, 'sc-l1': c['tongyong-guifan-l1'],
        'sc-l2': c['tongyong-guifan-l2'], 'sc-l3': c['tongyong-guifan-l3'],
        'jp': jp, 'kr': kr, 'kr-compat': c['ksx1001-hanja'] - han,
        'tw-sc': tw & sc, 'jp-tw': jp & tw, 'jp-sc': jp & sc,
        'kr-tw': kr & tw, 'kr-sc': kr & sc,
        'jp-only': jp - (tw | sc | kr), 'kr-only': kr - (tw | sc | jp),
        'kr-sc-not-tw': (kr & sc) - tw,
        'kana': kana,
        'hiragana': hira, 'katakana': kata, 'kana-ext': kana_ext,
        'kana-halfwidth': c['halfwidth-kana'],
        'hangul': c['hangul-syllables'], 'hangul-common': c['ksx1001-hangul'],
        'jamo': blocks('Hangul Jamo', 'Hangul Compatibility Jamo',
                       'Hangul Jamo Extended-A', 'Hangul Jamo Extended-B'),
        'bopomofo': bopomofo,
    }


def cjk_coverage(cps: frozenset[int], sets: dict[str, frozenset[int]]) -> dict:
    return {key: [len(cps & subset), len(subset)] for key, subset in sets.items()}


def refresh_cjk_details(entries: list[dict], site_data: Path, downloads_dir: Path,
                        charsets: list[Charset], ucd: Ucd) -> None:
    """Enrich both new and cached families without regenerating glyph assets.

    Canonical downloadable BDFs already have Unicode encodings, including PCF
    sources. Only read their ENCODING lines; this also avoids rasterizing fonts.
    The signature covers definitions and every variant's BDF hash.
    """
    sets = cjk_sets(charsets, ucd)
    definitions = json.dumps({k: sorted(v) for k, v in sets.items()}, sort_keys=True)
    definition_hash = hashlib.sha256(definitions.encode()).hexdigest()
    for entry in entries:
        path = site_data / 'details' / f"{entry['slug']}.json"
        detail = json.loads(path.read_text(encoding='utf-8'))
        bdfs = [d for d in detail['downloads'] if d['kind'] == 'bdf']
        signature = hashlib.sha256(json.dumps([
            definition_hash, [(d['variantId'], d['sha256']) for d in bdfs],
        ]).encode()).hexdigest()
        if detail.get('cjkCoverageSignature') == signature:
            continue
        coverage = {}
        for item in bdfs:
            source = downloads_dir / item['file']
            raw = gzip.decompress(source.read_bytes()) if source.suffix == '.gz' else source.read_bytes()
            cps = frozenset(int(cp) for cp in re.findall(rb'^ENCODING (\d+)\r?$', raw, re.M))
            coverage[item['variantId']] = cjk_coverage(cps, sets)
        expected = {v['id'] for v in entry['variants']}
        if set(coverage) != expected:
            raise ValueError(f"{entry['slug']}: missing canonical BDF for CJK coverage")
        detail['cjkCoverage'] = coverage
        detail['cjkCoverageSignature'] = signature
        path.write_text(json.dumps(detail, ensure_ascii=False, sort_keys=True,
                                   separators=(',', ':')) + '\n', encoding='utf-8')
