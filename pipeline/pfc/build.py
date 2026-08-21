"""构建编排器:fonts/ → site/public/data + dist-downloads(契约 C5/C6/C8)。

用法:python -m pfc.build --fonts fonts --out site/public/data \
        --downloads dist-downloads --cache .cache [--family <slug>]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from pfc.cache import FamilyCache, data_dir_hash, family_key
from pfc.coverage.charsets import DATA_DIR, load_charsets
from pfc.coverage.engine import (
    badges,
    coverage_for,
    detect_scripts,
    font_cps,
    overview,
    pick_sample_lang,
    unicode_block_coverage,
)
from pfc.coverage.ucd import load_ucd
from pfc.downloads import build_downloads
from pfc.familymeta import FamilyMeta, VariantDesc, load_family_meta, resolve_variant
from pfc.glyphpack import write_packs
from pfc.licenses import detect_license
from pfc.metrics import InkMetrics, claimed_size, compute_ink, is_monospaced
from pfc.model import ParsedFont
from pfc.parsers.bdf import parse_bdf
from pfc.parsers.pcf import parse_pcf
from pfc.prerender import og_png, sample_svg
from pfc.samples import SAMPLES

_SUMMARY_IDS = [
    "gb2312", "tongyong-guifan", "big5-changyong", "tw-changyong-4808",
    "jisx0208-l1", "ksx1001-hangul", "hangul-syllables", "wgl4", "cp437",
    "latin-basic", "hiragana", "katakana",
]

_FONT_SUFFIXES = (".bdf", ".bdf.gz", ".pcf", ".pcf.gz")


@dataclass
class BuiltVariant:
    desc: VariantDesc
    font: ParsedFont
    ink: InkMetrics
    coverage: dict[str, tuple[int, int]]
    blocks: list
    overview: dict


@dataclass
class BuildReport:
    families: int = 0
    variants: int = 0
    cached: int = 0
    data_bytes: int = 0
    warnings: list[str] = field(default_factory=list)
    took_s: float = 0.0


def _font_files(family_dir: Path) -> list[Path]:
    out = [
        p for p in sorted(family_dir.iterdir())
        if p.is_file() and p.name.lower().endswith(_FONT_SUFFIXES)
    ]
    return out


def _parse(path: Path, slug: str) -> ParsedFont:
    if ".pcf" in path.name.lower():
        return parse_pcf(path, slug)
    return parse_bdf(path, slug)


def _ratio(cov: dict[str, tuple[int, int]], cid: str) -> float:
    if cid not in cov:
        return 0.0
    have, total = cov[cid]
    return have / total if total else 0.0


def _json_dump(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def _build_family(
    family_dir: Path, site_data: Path, downloads_dir: Path,
    charsets, ucd, han_ref, report: BuildReport,
) -> tuple[dict, dict]:
    """返回 (index_entry, cache_payload)。"""
    slug = family_dir.name
    meta = load_family_meta(family_dir)
    files = _font_files(family_dir)

    built: list[BuiltVariant] = []
    seen_ids: set[str] = set()
    for p in files:
        f = _parse(p, slug)
        v = resolve_variant(f, meta)
        if v.id in seen_ids:
            base = v.id
            n = 2
            while f"{base}-{n}" in seen_ids:
                n += 1
            v.id = f"{base}-{n}"
            report.warnings.append(f"{slug}: variant id collision for {base}")
        seen_ids.add(v.id)
        cps = font_cps(f)
        cov = coverage_for(cps, charsets)
        built.append(BuiltVariant(
            desc=v, font=f, ink=compute_ink(f, han_ref), coverage=cov,
            blocks=unicode_block_coverage(cps, ucd), overview=overview(cps, ucd),
        ))
    if not built:
        raise ValueError(f"{slug}: no font files")

    license_info = detect_license(family_dir, [b.font for b in built],
                                  meta.license_override)

    # 家族级聚合
    best = max(built, key=lambda b: len(b.font.glyphs))
    fam_badges: list[str] = []
    for b in built:
        for bd in badges(b.coverage):
            if bd not in fam_badges:
                fam_badges.append(bd)
    scripts: list[str] = []
    for b in built:
        for s in detect_scripts(b.coverage):
            if s not in scripts:
                scripts.append(s)
    sample_lang = pick_sample_lang(best.coverage)
    sample_text = meta.samples.get(sample_lang) or SAMPLES.get(sample_lang, SAMPLES["latin"])

    # 资产
    for b in built:
        write_packs(b.font, b.desc, meta.name, site_data / "packs" / slug / b.desc.id)
    preview_rel = f"previews/{slug}/{sample_lang}.svg"
    (site_data / "previews" / slug).mkdir(parents=True, exist_ok=True)
    (site_data / "previews" / slug / f"{sample_lang}.svg").write_text(
        sample_svg(best.font, sample_text), encoding="utf-8"
    )
    og_png(best.font, meta.name, sample_text, site_data / "og" / f"{slug}.png")

    dl_entries = build_downloads(
        slug, family_dir, [(b.font, b.desc) for b in built],
        [license_info.file] if license_info.file else [],
        f"{meta.name}\n来源: {meta.provenance or meta.homepage or '-'}\n"
        f"许可证: {license_info.name}\n由 点阵字库 Pixel Font Collection 打包\n",
        downloads_dir,
    )

    han_ink_by_size: dict[str, list[int]] = {}
    for b in built:
        if b.ink.han_ink and str(b.desc.size) not in han_ink_by_size:
            han_ink_by_size[str(b.desc.size)] = list(b.ink.han_ink)
    ink_height = 0
    for b in built:
        h = b.ink.han_ink[1] if b.ink.han_ink else (b.ink.cap_height or 0)
        ink_height = max(ink_height, h)

    entry = {
        "slug": slug,
        "name": meta.name,
        "nameZh": meta.name_zh,
        "author": meta.author,
        "form": meta.form,
        "vibes": meta.vibes,
        "scripts": scripts,
        "sizes": sorted({b.desc.size for b in built}),
        "weights": sorted({b.desc.weight for b in built}),
        "spacing": sorted({b.desc.spacing for b in built}),
        "license": {
            "spdx": license_info.spdx,
            "name": license_info.name,
            "commercial": license_info.commercial,
            "confidence": license_info.confidence,
        },
        "converted": bool(meta.converted_from),
        "curated": meta.curated,
        "glyphCount": max(len(b.font.glyphs) for b in built),
        "hanInk": han_ink_by_size or None,
        "inkHeight": ink_height,
        "badges": fam_badges,
        "coverageSummary": {
            cid: round(max(_ratio(b.coverage, cid) for b in built), 4)
            for cid in _SUMMARY_IDS
        },
        "variants": [
            {
                "id": b.desc.id,
                "file": b.desc.file,
                "size": b.desc.size,
                "weight": b.desc.weight,
                "spacing": b.desc.spacing,
                "script": b.desc.script_subset,
                "glyphs": len(b.font.glyphs),
            }
            for b in built
        ],
        "preview": preview_rel,
        "sampleLang": sample_lang,
        "added": meta.added,
    }

    detail = {
        "slug": slug,
        "meta": entry,
        "homepage": meta.homepage,
        "repository": meta.repository,
        "description": meta.description,
        "provenance": meta.provenance,
        "convertedFrom": meta.converted_from,
        "licenseText": license_info.file,
        "licenseNote": license_info.note,
        "warnings": sorted({w for b in built for w in b.font.warnings}),
        "metrics": {
            b.desc.id: {
                "pixelSize": claimed_size(b.font),
                "ascent": b.font.ascent,
                "descent": b.font.descent,
                "bbox": list(b.font.bbox),
                "hanInk": list(b.ink.han_ink) if b.ink.han_ink else None,
                "capHeight": b.ink.cap_height,
                "xHeight": b.ink.x_height,
                "maxInk": list(b.ink.max_ink),
                "maxInkCps": list(b.ink.max_ink_cps),
                "monospaced": is_monospaced(b.font),
                "dwidthHistogram": _dwidth_hist(b.font),
            }
            for b in built
        },
        "coverage": {
            b.desc.id: {cid: list(v) for cid, v in b.coverage.items()}
            for b in built
        },
        "overview": {
            b.desc.id: {
                "total": list(b.overview["total"]),
                "planes": [list(p) for p in b.overview["planes"]],
                "pua": [list(p) for p in b.overview["pua"]],
                "hanTotal": list(b.overview["han_total"]),
                "compat": list(b.overview["compat"]),
                "compatUnifiedNote": list(b.overview["compat_unified_note"]),
            }
            for b in built
        },
        "unicodeBlocks": {
            b.desc.id: [list(row) for row in b.blocks] for b in built
        },
        "downloads": dl_entries,
    }
    _json_dump(detail, site_data / "details" / f"{slug}.json")

    report.variants += len(built)
    cache_payload = {"index_entry": entry, "downloads": dl_entries}
    return entry, cache_payload


def _dwidth_hist(f: ParsedFont) -> dict[str, int]:
    counts: dict[int, int] = {}
    for g in f.glyphs:
        counts[g.dwidth] = counts.get(g.dwidth, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    return {str(k): v for k, v in top}


def _outputs_exist(site_data: Path, entry: dict) -> bool:
    slug = entry["slug"]
    if not (site_data / "details" / f"{slug}.json").exists():
        return False
    for v in entry["variants"]:
        if not (site_data / "packs" / slug / v["id"] / "manifest.json").exists():
            return False
    return True


def build(fonts_dir: Path, site_data: Path, downloads_dir: Path, cache_dir: Path,
          only_family: str | None = None) -> BuildReport:
    t0 = time.monotonic()
    report = BuildReport()
    charsets = load_charsets(DATA_DIR)
    ucd = load_ucd(DATA_DIR / "ucd")
    han_ref = next(c.cps for c in charsets if c.id == "tongyong-guifan-l1")
    data_hash = data_dir_hash(DATA_DIR)
    cache = FamilyCache(cache_dir)
    site_data.mkdir(parents=True, exist_ok=True)
    downloads_dir.mkdir(parents=True, exist_ok=True)

    entries: list[dict] = []
    all_downloads: list[dict] = []
    for family_dir in sorted(p for p in fonts_dir.iterdir() if p.is_dir()):
        slug = family_dir.name
        if slug.startswith("."):
            continue
        files = _font_files(family_dir)
        if not files:
            report.warnings.append(f"{slug}: 目录中无字体文件,跳过")
            continue
        if not (family_dir / "family.toml").exists():
            load_family_meta(family_dir)  # 物化 stub,保证缓存键稳定
        key = family_key(data_hash, family_dir, files)
        cached = cache.load(slug, key)
        if only_family and slug != only_family:
            if cached and _outputs_exist(site_data, cached["index_entry"]):
                entries.append(cached["index_entry"])
                all_downloads.extend(cached["downloads"])
                report.cached += 1
                report.families += 1
            continue
        if cached and _outputs_exist(site_data, cached["index_entry"]):
            entries.append(cached["index_entry"])
            all_downloads.extend(cached["downloads"])
            report.cached += 1
            report.families += 1
            print(f"  {slug}: cached")
            continue
        entry, payload = _build_family(
            family_dir, site_data, downloads_dir, charsets, ucd, han_ref, report
        )
        payload["key"] = key
        cache.store(slug, payload)
        entries.append(entry)
        all_downloads.extend(payload["downloads"])
        report.families += 1
        print(f"  {slug}: built ({len(entry['variants'])} variants)")

    entries.sort(key=lambda e: e["slug"])
    _json_dump(
        {"generatedAt": "", "families": entries},
        site_data / "index.json",
    )
    _json_dump({"entries": all_downloads}, downloads_dir / "manifest.json")

    report.data_bytes = sum(p.stat().st_size for p in site_data.rglob("*") if p.is_file())
    report.took_s = time.monotonic() - t0
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--downloads", type=Path, required=True)
    ap.add_argument("--cache", type=Path, required=True)
    ap.add_argument("--family", default=None)
    ap.add_argument("--budget-mb", type=int, default=900)
    args = ap.parse_args()
    report = build(args.fonts, args.out, args.downloads, args.cache, args.family)
    mb = report.data_bytes / 1048576
    print(f"families={report.families} variants={report.variants} "
          f"cached={report.cached} data={mb:.1f}MB took={report.took_s:.1f}s")
    for w in report.warnings:
        print(f"  warn: {w}")
    if mb > args.budget_mb:
        print(f"ERROR: 站点数据 {mb:.0f}MB 超过预算 {args.budget_mb}MB", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
