"""Fixed SVG specimens built from the same BDFs offered for download."""
from __future__ import annotations

import hashlib
from pathlib import Path

from opf.parsers.bdf import parse_bdf
from opf.model import ParsedFont
from opf.prerender import og_png, sample_svg
from opf.samples import SAMPLES, sample_is_broken, specimen
from opf.coverage.engine import pick_sample_lang

_PREVIEW_SCRIPTS = ("zh-Hans", "zh-Hant", "ja", "ko", "latin")


def default_variant_rank(size: int, glyphs: int) -> tuple[bool, int]:
    """Prefer 8–16px inclusive, then the most glyphs; preserve input order on ties."""
    return 8 <= size <= 16, glyphs


def default_sample(meta, coverage: dict, font: ParsedFont) -> tuple[str, str]:
    """Keep fresh builds and cached preview selection on the same sample policy."""
    script = meta.sample_lang or pick_sample_lang(coverage)
    text = meta.samples.get(script) or SAMPLES.get(script, SAMPLES["latin"])
    cps = {g.cp for g in font.glyphs}
    if not meta.samples.get(script) and sample_is_broken(text, cps):
        text = specimen(cps) or text
    return script, text


def pick_variant(variants: list[dict], script: str, preferred_id: str) -> dict:
    """Prefer native glyph forms, preserving the default size/weight/layout."""
    preferred = next((v for v in variants if v["id"] == preferred_id), variants[0])
    candidates = [v for v in variants if v["script"] == script]
    if not candidates:
        candidates = [v for v in variants if v["script"] is None] or variants

    def rank(v):
        # Prefer the general Traditional/Taiwan form over HK/inherited forms.
        tail = v["id"].lower().replace("_", "-").split("-")[-1]
        regional = script == "zh-Hant" and tail in ("hant", "tw", "tc")
        return (v["size"] == preferred["size"],
                v["weight"] == preferred["weight"],
                v["spacing"] == preferred["spacing"],
                v["width"] == preferred["width"], regional,
                v["glyphs"], v["id"] == preferred_id)

    return max(candidates, key=rank)


def refresh_previews(entry: dict, meta, data: Path, downloads: Path,
                     fonts: dict[str, ParsedFont] | None = None) -> None:
    variants = entry["variants"]
    scripts = {v["script"] for v in variants} - {None}
    loaded = dict(fonts or {})

    def get_font(variant_id: str) -> ParsedFont:
        if variant_id not in loaded:
            loaded[variant_id] = parse_bdf(
                downloads / f"{entry['slug']}--{variant_id}.bdf.gz", entry["slug"])
        return loaded[variant_id]

    preferred_id = entry["previewVariant"]
    # A language-specific counterpart must not move the default specimen outside
    # the preferred range. Explicit per-family overrides retain their priority.
    default_variants = variants if meta.default_variant else (
        [v for v in variants if 8 <= v["size"] <= 16] or variants)
    slug = entry["slug"]
    folder = data / "previews" / slug
    folder.mkdir(parents=True, exist_ok=True)
    previews = {}
    for script in dict.fromkeys([entry["sampleLang"], *_PREVIEW_SCRIPTS]):
        is_default = script == entry["sampleLang"]
        if not is_default and script not in scripts:
            continue
        variant = (pick_variant(default_variants if is_default else variants, script, preferred_id) if scripts else
                   next(v for v in variants if v["id"] == preferred_id))
        text = entry["sampleText"] if is_default else meta.samples.get(script) or SAMPLES[script]
        font = get_font(variant["id"])
        cps = {g.cp for g in font.glyphs}
        if sample_is_broken(text, cps):
            if is_default:
                variant = next(v for v in variants if v["id"] == preferred_id)
                font = get_font(variant["id"])
            else:
                # Some locale variants supply only part of the script (Jelly
                # Pixel's Chinese, Ark Pixel's Hanja). Show available native
                # glyphs rather than choosing another locale or missing boxes.
                ranges = {
                    "zh-Hans": [(0x3400, 0xA000), (0x20000, 0x32400)],
                    "zh-Hant": [(0x3400, 0xA000), (0x20000, 0x32400)],
                    "ja": [(0x3040, 0x3100)],
                    "ko": [(0x1100, 0x1200), (0x3130, 0x3190), (0xAC00, 0xD7B0)],
                    "latin": [(0x20, 0x250)],
                }[script]
                native = {cp for cp in cps if any(lo <= cp < hi for lo, hi in ranges)}
                text = specimen(native or cps)
        file = f"previews/{slug}/{script}.svg"
        (data / file).write_text(sample_svg(font, text), encoding="utf-8")
        previews[script] = {"variantId": variant["id"], "text": text, "file": file}
        if is_default:
            entry["previewVariant"] = variant["id"]
            entry["preview"] = file
            og_png(font, meta.name, text, data / "og" / f"{slug}.png")
    entry["previews"] = previews

    default_font = get_font(entry["previewVariant"])
    card = f"previews/{slug}/card.svg"
    (data / card).write_text(sample_svg(default_font, entry["sampleText"], max_width=120), encoding="utf-8")
    entry["cardPreview"] = card
    names = dict.fromkeys([meta.name, meta.name_en, *entry.get("names", {}).values()])
    available = {g.cp for g in default_font.glyphs}
    title_previews = {}
    for name in names:
        if not name or not {ord(c) for c in name} <= available:
            continue
        file = f"previews/{slug}/name-{hashlib.sha256(name.encode()).hexdigest()[:12]}.svg"
        (data / file).write_text(sample_svg(default_font, name), encoding="utf-8")
        title_previews[name] = file
    entry["namePreviews"] = title_previews
    keep = {Path(card).name, *(Path(v["file"]).name for v in previews.values()),
            *(Path(file).name for file in title_previews.values())}
    for old in folder.glob("*.svg"):
        if old.name not in keep:
            old.unlink()
