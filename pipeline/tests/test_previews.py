from dataclasses import replace
from pathlib import Path

import pytest

from opf.familymeta import FamilyMeta, resolve_variant
import gzip
from opf.ingest.bdfwrite import write_bdf
from opf.parsers.bdf import parse_bdf
from opf.previews import default_variant_rank, pick_variant, refresh_previews
from opf.prerender import sample_svg


def variant(id, script=None, **overrides):
    return dict(id=id, script=script, size=12, weight="regular",
                spacing="proportional", width="normal", glyphs=100, **overrides)


@pytest.mark.parametrize("sizes, expected", [
    ([(10, 1661), (13, 3298), (20, 5263)], 13),
    ([(7, 1000), (8, 100)], 8),
    ([(16, 100), (17, 1000)], 16),
    ([(7, 100), (20, 1000)], 20),
    ([(8, 200), (16, 100)], 8),
])
def test_default_size_window_precedes_glyph_count(sizes, expected):
    assert max(sizes, key=lambda v: default_variant_rank(*v))[0] == expected


@pytest.mark.parametrize("script", ["zh-Hans", "zh-Hant", "ja", "ko"])
def test_native_forms_win_over_glyph_count_and_preserve_style(script):
    latin = variant("12px-latin", "latin")
    native = variant(f"12px-{script}", script)
    other_size = {**native, "id": f"16px-{script}", "size": 16, "glyphs": 200}
    assert pick_variant([latin, other_size, native], script, latin["id"]) == native
    assert pick_variant([latin, native], "latin", native["id"]) == latin


def test_neutral_variant_is_preferred_to_foreign_glyph_forms():
    ja, neutral = variant("jp", "ja"), variant("default")
    assert pick_variant([ja, neutral], "zh-Hans", "jp") == neutral
    assert pick_variant([ja], "zh-Hans", "jp") == ja


def test_traditional_prefers_taiwan_to_hong_kong_when_both_available():
    variants = [variant("zh_hk", "zh-Hant"), variant("zh_tw", "zh-Hant")]
    assert pick_variant(variants, "zh-Hant", "zh_hk")["id"] == "zh_tw"


def test_cached_previews_render_native_glyphs_including_chars_outside_core(tmp_path):
    font = parse_bdf(Path(__file__).parent / "fixtures" / "mini.bdf", "mini")
    meta = FamilyMeta(slug="mini", name="A", samples={"ja": "永", "zh-Hans": "永"})
    desc = resolve_variant(font, meta)
    native = replace(font, glyphs=[replace(g, rows=bytes(len(g.rows))) for g in font.glyphs])
    for id, source in [("ja", font), ("zh", native)]:
        raw = tmp_path / "font.bdf"
        write_bdf(source, raw)
        (tmp_path / f"mini--{id}.bdf.gz").write_bytes(gzip.compress(raw.read_bytes()))
    entry = {"slug": "mini", "variants": [variant("ja", "ja"), variant("zh", "zh-Hans")],
             "previewVariant": "ja", "sampleLang": "zh-Hans", "sampleText": "永"}
    refresh_previews(entry, meta, tmp_path, tmp_path)
    assert entry["sampleLang"] == "zh-Hans"
    assert entry["sampleText"] == "永"
    assert entry["previewVariant"] == "zh"
    assert entry["previews"]["ja"]["variantId"] == "ja"
    assert (tmp_path / entry["preview"]).read_text() == sample_svg(native, "永")
    assert (tmp_path / entry["previews"]["ja"]["file"]).read_text() == sample_svg(font, "永")
    first = (tmp_path / entry["preview"]).read_bytes()
    refresh_previews(entry, meta, tmp_path, tmp_path)
    assert (tmp_path / entry["preview"]).read_bytes() == first


def test_partial_native_coverage_uses_available_glyphs_instead_of_foreign_variant(tmp_path):
    font = parse_bdf(Path(__file__).parent / "fixtures" / "mini.bdf", "mini")
    meta = FamilyMeta(slug="mini", name="永")
    desc = resolve_variant(font, meta)
    for id in ("latin", "zh"):
        raw = tmp_path / "font.bdf"
        write_bdf(font, raw)
        (tmp_path / f"mini--{id}.bdf.gz").write_bytes(gzip.compress(raw.read_bytes()))
    entry = {"slug": "mini", "variants": [variant("latin", "latin"), variant("zh", "zh-Hans")],
             "previewVariant": "latin", "sampleLang": "latin", "sampleText": "A"}
    refresh_previews(entry, meta, tmp_path, tmp_path)
    native = entry["previews"]["zh-Hans"]
    assert native["variantId"] == "zh"
    assert native["text"] == "永"
    assert 'class="missing"' not in (tmp_path / native["file"]).read_text()
