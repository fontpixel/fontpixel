from pathlib import Path

from opf.familymeta import load_family_meta, resolve_variant
from opf.model import ParsedFont

TOML = """
name = "Fusion Pixel"
name_zh = "缝合像素"
authors = ["TakWolf", "pixel-font-studio"]
homepage = "https://fusion-pixel-font.takwolf.com"
repository = "https://github.com/TakWolf/fusion-pixel-font"
description = "多来源缝合的像素字体"
form = "gothic"
vibes = ["retro-game", "cute"]
aliases = ["FZG", "缝合怪"]
converted_from = ""
provenance = "官方 release BDF"

[license]
spdx = "OFL-1.1"
file = "LICENSE-OFL"

[samples]
zh-Hans = "缝合怪也有春天"

[variants."fusion-pixel-10px-monospaced-zh_hans.bdf"]
display = "10px 等宽 简体"
weight = "regular"
"""


def _font(file_name: str, props: dict, pixel_size: int = 10,
          dwidths: list[int] | None = None) -> ParsedFont:
    from opf.model import Glyph

    glyphs = []
    for i, dw in enumerate(dwidths or [8, 8, 8, 8]):
        glyphs.append(Glyph(cp=0x4E00 + i, name=f"g{i}", dwidth=dw, bbw=1, bbh=1,
                            bbx=0, bby=0, rows=b"\x80"))
    return ParsedFont(
        path=Path(file_name), family_slug="fam", file_name=file_name, props=props,
        pixel_size=pixel_size, ascent=9, descent=1, bbox=(10, 10, 0, -1),
        glyphs=glyphs, warnings=[],
    )


def test_load_full_toml(tmp_path):
    d = tmp_path / "fusion-pixel"
    d.mkdir()
    (d / "family.toml").write_text(TOML, encoding="utf-8")
    m = load_family_meta(d)
    assert m.slug == "fusion-pixel"
    assert m.name == "Fusion Pixel"
    assert m.name_zh == "缝合像素"
    assert m.form == "gothic"
    assert m.vibes == ["retro-game", "cute"]
    assert m.aliases == ["FZG", "缝合怪"]
    assert m.authors == ["TakWolf", "pixel-font-studio"]
    assert m.curated is True
    assert m.license_override == {"spdx": "OFL-1.1", "file": "LICENSE-OFL"}
    assert m.samples == {"zh-Hans": "缝合怪也有春天"}
    assert "fusion-pixel-10px-monospaced-zh_hans.bdf" in m.variant_overrides


def test_legacy_singular_author_still_loads(tmp_path):
    # the legacy singular author = "..." form must still load, so a missed file doesn't silently drop its author
    d = tmp_path / "old"
    d.mkdir()
    (d / "family.toml").write_text('name = "Old"\nauthor = "TakWolf"\n',
                                   encoding="utf-8")
    m = load_family_meta(d)
    assert m.authors == ["TakWolf"]


def test_authors_default_to_empty(tmp_path):
    d = tmp_path / "anon"
    d.mkdir()
    (d / "family.toml").write_text('name = "Anon"\n', encoding="utf-8")
    assert load_family_meta(d).authors == []


def test_aliases_default_to_empty(tmp_path):
    # most families have no aliases; a missing key should not be an error
    d = tmp_path / "plain"
    d.mkdir()
    (d / "family.toml").write_text('name = "Plain"\n', encoding="utf-8")
    assert load_family_meta(d).aliases == []


def test_missing_toml_writes_stub(tmp_path):
    d = tmp_path / "cool-font"
    d.mkdir()
    m = load_family_meta(d)
    assert m.curated is False
    assert m.name == "Cool Font"
    stub = (d / "family.toml").read_text(encoding="utf-8")
    assert "TODO" in stub
    m2 = load_family_meta(d)  # the stub can be read back
    assert m2.name == "Cool Font"


def test_resolve_variant_from_props_and_filename(tmp_path):
    d = tmp_path / "fusion-pixel"
    d.mkdir()
    (d / "family.toml").write_text(TOML, encoding="utf-8")
    m = load_family_meta(d)

    f = _font("fusion-pixel-10px-monospaced-zh_hans.bdf",
              {"WEIGHT_NAME": "Regular", "SPACING": "M"})
    v = resolve_variant(f, m)
    assert v.id == "fusion-pixel-10px-monospaced-zh_hans"
    assert v.size == 10
    assert v.weight == "regular"
    assert v.spacing == "monospaced"
    assert v.script_subset == "zh-Hans"
    assert v.display == "10px 等宽 简体"  # override takes effect


def test_resolve_bold_from_filename_suffix(tmp_path):
    d = tmp_path / "baekmuk-batang"
    d.mkdir()
    m = load_family_meta(d)
    v = resolve_variant(_font("batang16b.bdf", {}, pixel_size=16), m)
    assert v.weight == "bold"
    assert v.size == 16


def test_resolve_spacing_fallback_measured(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    m = load_family_meta(d)
    mono = resolve_variant(_font("a.bdf", {}, dwidths=[8] * 200), m)
    assert mono.spacing == "monospaced"
    prop = resolve_variant(_font("b.bdf", {}, dwidths=[4, 8] * 100), m)
    assert prop.spacing == "proportional"


def test_variant_id_sanitized(tmp_path):
    d = tmp_path / "x"
    d.mkdir()
    m = load_family_meta(d)
    v = resolve_variant(_font("My Font (v2).bdf", {}), m)
    assert v.id == "My-Font--v2-"
