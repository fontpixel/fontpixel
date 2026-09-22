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
from opf.coverage.engine import han_counts, unified_han
from opf.coverage.ucd import Ucd

CJK_TABLE_KEYS = ('han', 'combined', 'tw', 'kr', 'kr-compat', 'kana',
                  'kana-marks', 'kana-ext', 'jamo', 'jamo-ext')


def cjk_sets(charsets: list[Charset], ucd: Ucd) -> dict[str, frozenset[int]]:
    c = {item.id: item.cps for item in charsets}

    def blocks(*names: str) -> frozenset[int]:
        return frozenset(cp for name, a, b in ucd.blocks if name in names
                         for cp in range(a, b + 1) if cp in ucd.assigned)

    han = unified_han(ucd)
    tw = c['tw-changyong-4808'] | c['tw-cichangyong-6343']
    sc, jp = c['tongyong-guifan'], c['jisx0208-l1']
    kr = c['ksx1001-hanja'] & han
    hira, kata = c['hiragana'], c['katakana']
    kana_marks = blocks('Hiragana', 'Katakana') - (hira | kata)
    kana_ext = blocks('Katakana Phonetic Extensions', 'Kana Supplement',
                      'Kana Extended-A', 'Kana Extended-B', 'Small Kana Extension')
    union = tw | sc | jp | kr
    kana = hira | kata | kana_marks | kana_ext | c['halfwidth-kana']
    jamo_ext = blocks('Hangul Jamo Extended-A', 'Hangul Jamo Extended-B')
    bopomofo = c['bopomofo']
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
        'tw-sc-union': tw | sc,
        'tw-sc-jp-union': tw | sc | jp, 'tw-sc-kr-union': tw | sc | kr,
        'tw-sc': tw & sc, 'jp-tw': jp & tw, 'jp-sc': jp & sc,
        'kr-tw': kr & tw, 'kr-sc': kr & sc,
        'tw-sc-jp': tw & sc & jp, 'tw-sc-kr': tw & sc & kr,
        'tw-sc-jp-kr': tw & sc & jp & kr,
        'tw-only': tw - (sc | jp | kr), 'sc-only': sc - (tw | jp | kr),
        'jp-only': jp - (tw | sc | kr), 'kr-only': kr - (tw | sc | jp),
        'kana': kana,
        'hiragana': hira, 'katakana': kata, 'kana-marks': kana_marks, 'kana-ext': kana_ext,
        'kana-halfwidth': c['halfwidth-kana'],
        'hangul': c['hangul-syllables'], 'hangul-common': c['ksx1001-hangul'],
        'jamo': c['hangul-jamo'] | c['hangul-compat-jamo'] | jamo_ext,
        'jamo-ext': jamo_ext,
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
    definitions = json.dumps({'sets': {k: sorted(v) for k, v in sets.items()},
                              'missingCharts': CJK_TABLE_KEYS}, sort_keys=True)
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
            variant = item['variantId']
            coverage[variant] = cjk_coverage(cps, sets)
            # Refresh old cached overview counts too: the map and overview must
            # classify the 12 unified ideographs in the compatibility block alike.
            if variant in detail.get('overview', {}):
                counts = han_counts(cps, ucd)
                detail['overview'][variant].update(
                    hanTotal=list(counts['han_total']), compat=list(counts['compat']),
                    compatUnifiedNote=list(counts['compat_unified_note']))
            missing = detail.setdefault('missingChars', {}).setdefault(variant, {})
            for key in CJK_TABLE_KEYS:
                absent = sets[key] - cps
                if 0 < len(absent) <= 500:
                    missing[key] = ''.join(chr(cp) for cp in sorted(absent))
                else:
                    missing.pop(key, None)
        expected = {v['id'] for v in entry['variants']}
        if set(coverage) != expected:
            raise ValueError(f"{entry['slug']}: missing canonical BDF for CJK coverage")
        detail['cjkCoverage'] = coverage
        detail['cjkCoverageSignature'] = signature
        path.write_text(json.dumps(detail, ensure_ascii=False, sort_keys=True,
                                   separators=(',', ':')) + '\n', encoding='utf-8')
