"""Build orchestrator: fonts/ → site/public/data + dist-downloads (contract C5/C6/C8).

Usage: python -m opf.build --fonts fonts --out site/public/data \
        --downloads dist-downloads --cache .cache [--family <slug>]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from opf import DATA_SCHEMA_VERSION
from opf.cache import FamilyCache, data_dir_hash, family_facts
from opf.coverage.charsets import DATA_DIR, load_charsets
from opf.coverage.engine import (
    badges,
    coverage_for,
    detect_scripts,
    font_cps,
    overview,
    pick_sample_lang,
    unicode_block_coverage,
)
from opf.coverage.ucd import load_ucd
from opf.downloads import build_downloads, refresh_downloads_metadata
from opf.familymeta import (
    FamilyMeta,
    VariantDesc,
    family_names,
    load_family_meta,
    resolve_variant,
)
from opf.glyphpack import write_packs
from opf.licenses import detect_license
from opf.mergesubsets import group_files, merge as merge_subsets
from opf.metrics import InkMetrics, claimed_size, compute_ink, is_monospaced
from opf.model import ParsedFont
from opf.parsers.bdf import parse_bdf
from opf.parsers.pcf import parse_pcf
from opf.prerender import og_png, sample_svg
from opf.samples import SAMPLES, sample_is_broken, specimen
from opf.variants import search_text

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
    failed: int = 0
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


def merge_scripts(scripts: list[str]) -> list[str]:
    """Take the best tier across variants at the family level.

    A family's scripts is the union across variants; a font where small
    sizes fall short of coverage but large sizes reach it (e.g. Ark Pixel)
    would otherwise show both zh-hans and zh-hans-partial, and having both
    labels side by side means nothing to a reader.
    """
    full = {s for s in scripts if not s.endswith("-partial")}
    return [
        s for s in scripts
        if not s.endswith("-partial") or s.removesuffix("-partial") not in full
    ]


def _build_family(
    family_dir: Path, site_data: Path, downloads_dir: Path,
    charsets, ucd, han_ref, report: BuildReport,
) -> tuple[dict, dict]:
    """Returns (index_entry, cache_payload)."""
    slug = family_dir.name
    meta = load_family_meta(family_dir)
    files = _font_files(family_dir)

    # Upstream sometimes ships stray files (placeholders with only a
    # glyph or two); filter those out.
    if meta.exclude:
        import fnmatch
        files = [
            p for p in files
            if not any(fnmatch.fnmatch(p.name, pat) for pat in meta.exclude)
        ]
    # Upstream often splits one typeface into several files (Latin in one,
    # CJK in another); listing them separately would show up as several
    # incomplete fonts, so merge them back into a single variant. Grouping
    # is automatic by filename, but a family can also specify groups explicitly.
    groups = group_files(files) if meta.merge_subsets else {p: [] for p in files}
    if meta.merge:
        by_name = {p.name: p for p in files}
        for base_name, sub_names in meta.merge.items():
            base = by_name.get(base_name)
            if base is None:
                report.warnings.append(f"{slug}: merge 基准文件不存在 {base_name}")
                continue
            subs = groups.setdefault(base, [])
            for n in sub_names:
                sp = by_name.get(n)
                if sp is None:
                    report.warnings.append(f"{slug}: merge 子文件不存在 {n}")
                    continue
                subs.extend([sp, *groups.pop(sp, [])])
            groups[base] = sorted(set(subs))

    # Parse each typeface first (merging where applicable); anything that
    # doesn't merge in still gets listed as its own variant, otherwise
    # those glyphs would just vanish.
    fonts: list[ParsedFont] = []
    for p in sorted(groups):
        f = _parse(p, slug)
        if groups[p]:
            f, notes, rejected = merge_subsets(
                f, [_parse(x, slug) for x in groups[p]]
            )
            f.warnings.extend(notes)
            fonts.extend(rejected)
        fonts.append(f)

    built: list[BuiltVariant] = []
    seen_ids: set[str] = set()
    for f in fonts:
        # No glyphs left at all means this typeface's charset never got
        # decoded (e.g. a proprietary encoding like Adobe FontSpecific) —
        # that's not "low coverage," it's "never parsed." Fail the whole
        # family build so the per-family isolation layer above records it
        # in the report — an empty font must never get published to the site.
        if not f.glyphs:
            raise ValueError(
                f"{f.file_name} 解析后一个字形都不剩"
                f"(CHARSET_REGISTRY={f.props.get('CHARSET_REGISTRY', '?')}, "
                f"CHARSET_ENCODING={f.props.get('CHARSET_ENCODING', '?')});"
                "多半是该字符集尚未支持,需先补码位映射再收录"
            )
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
        # Pure-CJK fonts (KS X 1001, JIS, etc.) often have zero ASCII, so
        # installing them means Latin letters and spaces fall back to
        # another font. That's not a bug, but the user should be told.
        if len(cps) > 200:
            latin = sum(1 for c in range(0x41, 0x7B) if c in cps)
            if latin == 0:
                f.warnings.append(
                    "不含任何 ASCII 字母，需搭配拉丁字体使用（上游即如此）"
                )
            if 0x20 not in cps:
                f.warnings.append(
                    "不含半角空格 U+0020"
                    + ("，站内预览按空白显示" if 0x3000 in cps else "")
                )
        cov = coverage_for(cps, charsets)
        built.append(BuiltVariant(
            desc=v, font=f, ink=compute_ink(f, han_ref), coverage=cov,
            blocks=unicode_block_coverage(cps, ucd), overview=overview(cps, ucd),
        ))
    if not built:
        raise ValueError(f"{slug}: no font files")
    # Sort variants by size so the on-page switcher isn't in filename order
    # (e.g. 13, 15, 16, 14, 12).
    _WEIGHT = {"light": 0, "regular": 1, "bold": 2}
    built.sort(key=lambda b: (b.desc.size, _WEIGHT.get(b.desc.weight, 9),
                              b.desc.spacing, b.desc.script_subset or ""))

    license_info = detect_license(family_dir, [b.font for b in built],
                                  meta.license_override)
    _cps_cache = {b.desc.id: font_cps(b.font) for b in built}

    # Family-level aggregation
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
    scripts = merge_scripts(scripts)
    sample_lang = meta.sample_lang or pick_sample_lang(best.coverage)
    sample_text = meta.samples.get(sample_lang) or SAMPLES.get(sample_lang, SAMPLES["latin"])
    # Icon/symbol fonts can't render any preset sample text, so fall back
    # to using their own glyphs.
    if not meta.samples.get(sample_lang):
        best_cps = font_cps(best.font)
        if sample_is_broken(sample_text, best_cps):
            sample_text = specimen(best_cps) or sample_text

    # Assets
    for b in built:
        write_packs(b.font, b.desc, meta.name, site_data / "packs" / slug / b.desc.id)
    preview_rel = f"previews/{slug}/{sample_lang}.svg"
    (site_data / "previews" / slug).mkdir(parents=True, exist_ok=True)
    (site_data / "previews" / slug / f"{sample_lang}.svg").write_text(
        sample_svg(best.font, sample_text), encoding="utf-8"
    )
    og_png(best.font, meta.name, sample_text, site_data / "og" / f"{slug}.png")

    if license_info.file and (family_dir / license_info.file).exists():
        lic_dir = site_data / "licenses"
        lic_dir.mkdir(parents=True, exist_ok=True)
        (lic_dir / f"{slug}.txt").write_bytes(
            (family_dir / license_info.file).read_bytes()
        )

    dl_entries = build_downloads(
        slug, family_dir, [(b.font, b.desc) for b in built],
        [license_info.file] if license_info.file else [],
        _readme_text(meta, license_info.name),
        downloads_dir,
        family_display=meta.name,
        copyright_line=_copyright_line(meta, license_info.name),
    )

    han_ink_by_size: dict[str, list[int]] = {}
    for b in built:
        if b.ink.han_ink and str(b.desc.size) not in han_ink_by_size:
            han_ink_by_size[str(b.desc.size)] = list(b.ink.han_ink)
    # Per-variant ink height: Han ink face height, or cap height as a
    # fallback when there's no Han. Sending only the family max would mean
    # a "14-14" size filter misses families that also have a 14px variant.
    ink_heights = sorted({
        b.ink.han_ink[1] if b.ink.han_ink else (b.ink.cap_height or 0)
        for b in built
    })
    ink_height = max(ink_heights, default=0)

    entry = {
        **_describe(meta, slug),
        "scripts": scripts,
        "sizes": sorted({b.desc.size for b in built}),
        "weights": sorted({b.desc.weight for b in built}),
        "spacing": sorted({b.desc.spacing for b in built}),
        "license": {
            "spdx": license_info.spdx,
            "name": license_info.name,
            "nameEn": license_info.name_en or license_info.name,
            "confidence": license_info.confidence,
        },
        "converted": bool(meta.converted_from),
        "glyphCount": max(len(b.font.glyphs) for b in built),
        "hanInk": han_ink_by_size or None,
        "inkHeight": ink_height,
        "inkHeights": ink_heights,
        "badges": fam_badges,
        "coverageSummary": {
            cid: round(max(_ratio(b.coverage, cid) for b in built), 4)
            for cid in _SUMMARY_IDS
        },
        # Family-level coverage across all charsets (max across variants),
        # in the same order as index.charsetIds
        "coverage": [
            round(max(_ratio(b.coverage, c.id) for b in built), 4) for c in charsets
        ],
        "variants": [
            {
                "id": b.desc.id,
                "file": b.desc.file,
                "size": b.desc.size,
                "weight": b.desc.weight,
                "spacing": b.desc.spacing,
                "width": b.desc.width,
                "displaySize": b.desc.display_size,
                "script": b.desc.script_subset,
                "glyphs": len(b.font.glyphs),
            }
            for b in built
        ],
        "preview": preview_rel,
        "sampleLang": sample_lang,
        # Sample text must be sent alongside the index: icon fonts use
        # their own glyphs, and the frontend looking sampleLang up in its
        # table would just get back English text that can't be rendered.
        "sampleText": sample_text,
        # The top preview uses the variant with the most glyphs; the input
        # box must match it, otherwise the two spots show different sizes
        # of the same font.
        "previewVariant": best.desc.id,
    }

    detail = {
        "slug": slug,
        "meta": entry,
        **_describe_detail(meta),
        "convertedFrom": meta.converted_from,
        "licenseText": license_info.file,
        "licenseNote": license_info.note,
        "licenseNoteEn": license_info.note_en or license_info.note,
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
        "missingChars": {
            b.desc.id: {
                c.id: "".join(chr(cp) for cp in sorted(missing))
                for c in charsets
                if 0 < len(missing := c.cps - _cps_cache[b.desc.id]) <= 500
            }
            for b in built
        },
        "downloads": dl_entries,
    }
    _json_dump(detail, site_data / "details" / f"{slug}.json")

    from opf.emit import cps_to_runs

    fam_cps: set[int] = set()
    for b in built:
        fam_cps |= font_cps(b.font)

    report.variants += len(built)
    cache_payload = {
        "index_entry": entry,
        "downloads": dl_entries,
        "runs": [list(r) for r in cps_to_runs(fam_cps)],
    }
    return entry, cache_payload


def _dwidth_hist(f: ParsedFont) -> dict[str, int]:
    counts: dict[int, int] = {}
    for g in f.glyphs:
        counts[g.dwidth] = counts.get(g.dwidth, 0) + 1
    top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:8]
    return {str(k): v for k, v in top}


def _readme_text(meta, license_name: str) -> str:
    """Provenance README bundled in the family zip. Shared between the full rebuild path and the metadata fast path."""
    return (f"{meta.name}\n来源：{meta.provenance or meta.homepage or '-'}\n"
            f"许可证：{license_name}\n由 开源像素字体馆 打包\n")


def _copyright_line(meta, license_name: str) -> str:
    """Copyright line written into the TTF name table. Shared between the full rebuild path and the metadata fast path."""
    return (f"{meta.name} — {license_name}"
            + (f"（{'、'.join(meta.authors)}）" if meta.authors else ""))



def _describe(meta, slug: str) -> dict:
    """The index entry fields that come purely from family.toml's display data.

    This is the single definition of "what counts as descriptive": the full
    rebuild path uses it to assemble the entry, and the cache-hit fast path
    uses it to refresh those fields. Add new fields here and both paths
    stay in sync; anything not listed here is structural by construction —
    changing it still triggers a rebuild (see cache._STRUCTURAL_KEYS).
    """
    return {
        "slug": slug,
        "name": meta.name,
        # All per-language spellings are sent; which one is shown is up to
        # the site based on interface language (i18n/pickName).
        "names": family_names(meta),
        "authors": meta.authors,
        "authorsEn": meta.authors_en or meta.authors,
        "form": meta.form,
        "vibes": meta.vibes,
        "curated": meta.curated,
        "added": meta.added,
        "searchText": _search_text_for(meta, slug),
    }


def _describe_detail(meta) -> dict:
    """The detail-page fields that come purely from family.toml's display data."""
    return {
        "homepage": meta.homepage,
        "repository": meta.repository,
        "description": meta.description,
        "descriptionEn": meta.description_en or meta.description,
        "provenance": meta.provenance,
        "provenanceEn": meta.provenance_en or meta.provenance,
    }


def _search_text_for(meta, slug: str) -> str:
    """The family's searchable text. After Simplified/Traditional expansion, searching "东云" also matches "東雲".

    name_en/author_en are what's shown on the English page — leaving them
    out means they can't be searched; aliases are former/alternate names
    (see family.toml).
    """
    return search_text(meta.name, *family_names(meta).values(),
                       " ".join(meta.authors), " ".join(meta.authors_en), slug,
                       " ".join(meta.vibes), " ".join(meta.aliases))


def _refresh_metadata(
    slug: str, family_dir: Path, site_data: Path, downloads_dir: Path,
    cached: dict,
) -> tuple[dict, list[dict]] | None:
    """Path taken when the glyph output is unchanged and only family.toml's display fields changed.

    The cache (see cache.facts_match) only tracks the font files and
    family.toml's structural fields, so after a cache hit the text in the
    index entry, detail page, and downloads may still be stale — this
    refreshes them, at a cost of a few milliseconds instead of re-vectorizing
    131 families for half an hour.

    Returns None when it can't refresh (output is missing), leaving the
    caller to fall back to a full rebuild.
    """
    meta = load_family_meta(family_dir)
    entry = {**cached["index_entry"], **_describe(meta, slug)}

    detail_path = site_data / "details" / f"{slug}.json"
    try:
        detail = json.loads(detail_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    detail.update(_describe_detail(meta))
    detail["meta"] = entry
    detail["convertedFrom"] = meta.converted_from

    license_name = entry["license"]["name"]
    dl_entries = refresh_downloads_metadata(
        cached["downloads"], downloads_dir,
        _readme_text(meta, license_name),
        meta.name, _copyright_line(meta, license_name),
    )
    if not dl_entries:
        return None
    detail["downloads"] = dl_entries
    _json_dump(detail, detail_path)
    return entry, dl_entries


def _outputs_exist(site_data: Path, entry: dict) -> bool:
    slug = entry["slug"]
    if not (site_data / "details" / f"{slug}.json").exists():
        return False
    for v in entry["variants"]:
        if not (site_data / "packs" / slug / v["id"] / "manifest.json").exists():
            return False
    return True


# Shared context for parallel rebuilds. Forked worker processes inherit it
# directly (zero-copy) rather than going through pickle — charsets/ucd run
# to tens of MB, and serializing them per task would eat up the whole gain
# from parallelizing.
_POOL_CTX: dict = {}


def _rebuild_one(args: tuple[str, str]) -> tuple[str, dict | None, dict | None,
                                                 int, list[str], str | None]:
    """Build one family in a worker process. Returns (slug, entry, payload, variant count, warnings, error)."""
    slug, family_dir = args
    ctx = _POOL_CTX
    local = BuildReport()          # worker collects its own warnings, merged back in the main process
    try:
        entry, payload = _build_family(
            Path(family_dir), ctx["site_data"], ctx["downloads_dir"],
            ctx["charsets"], ctx["ucd"], ctx["han_ref"], local,
        )
    except Exception as e:  # noqa: BLE001 - one family failing shouldn't take down the whole build
        return slug, None, None, 0, local.warnings, str(e)
    return slug, entry, payload, local.variants, local.warnings, None


def _jobs() -> int:
    """Parallelism: overridden by OPF_JOBS, capped at 8 by default — the
    largest families (unifont, mona) each need 1-2GB of memory during TTF
    export, and too much parallelism hits memory limits before CPU ones."""
    env = os.environ.get("OPF_JOBS", "").strip()
    if env:
        return max(1, int(env))
    return max(1, min(os.cpu_count() or 1, 8))


def _run_rebuilds(pending, site_data, downloads_dir, charsets, ucd, han_ref):
    """Dispatch families pending rebuild to the process pool; fall back to serial if fork is unavailable or there's only one task."""
    _POOL_CTX.update(site_data=site_data, downloads_dir=downloads_dir,
                     charsets=charsets, ucd=ucd, han_ref=han_ref)
    args = [(slug, str(d)) for slug, d, _ in pending]
    jobs = _jobs()
    if jobs <= 1 or len(args) <= 1:
        for a in args:
            yield _rebuild_one(a)
        return

    import multiprocessing as mp
    from concurrent.futures import ProcessPoolExecutor, as_completed
    try:
        mp_ctx = mp.get_context("fork")   # explicit fork: no longer the default as of Python 3.14
    except ValueError:
        for a in args:
            yield _rebuild_one(a)
        return

    # Queue large families first (estimated by directory size): something
    # like unifont shouldn't end up at the back of the queue dragging out the tail.
    size = {slug: sum(f.stat().st_size for f in d.iterdir() if f.is_file())
            for slug, d, _ in pending}
    args.sort(key=lambda a: -size[a[0]])
    with ProcessPoolExecutor(max_workers=min(jobs, len(args)),
                             mp_context=mp_ctx) as pool:
        futures = [pool.submit(_rebuild_one, a) for a in args]
        for fut in as_completed(futures):
            yield fut.result()


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
    runs_by_slug: dict[str, list[tuple[int, int]]] = {}
    pending: list[tuple[str, Path, dict]] = []
    for family_dir in sorted(p for p in fonts_dir.iterdir() if p.is_dir()):
        slug = family_dir.name
        if slug.startswith("."):
            continue
        files = _font_files(family_dir)
        if not files:
            report.warnings.append(f"{slug}: 目录中无字体文件，跳过")
            continue
        if not (family_dir / "family.toml").exists():
            load_family_meta(family_dir)  # materialize a stub so the cache key stays stable
        facts = family_facts(data_hash, family_dir)
        cached = cache.load(slug, facts)
        if only_family and slug != only_family:
            if cached and _outputs_exist(site_data, cached["index_entry"]):
                entries.append(cached["index_entry"])
                all_downloads.extend(cached["downloads"])
                runs_by_slug[slug] = [tuple(r) for r in cached.get("runs", [])]
                report.cached += 1
                report.families += 1
            continue
        if cached and _outputs_exist(site_data, cached["index_entry"]):
            refreshed = _refresh_metadata(
                slug, family_dir, site_data, downloads_dir, cached)
            if refreshed is not None:
                entry, dl_entries = refreshed
                entries.append(entry)
                all_downloads.extend(dl_entries)
                runs_by_slug[slug] = [tuple(r) for r in cached.get("runs", [])]
                if dl_entries != cached["downloads"]:
                    cached["downloads"] = dl_entries
                    cached["index_entry"] = entry
                    cached["facts"] = facts
                    cache.store(slug, cached)
                report.cached += 1
                report.families += 1
                print(f"  {slug}: cached")
                continue
        pending.append((slug, family_dir, facts))

    # Families needing a rebuild run in parallel across CPUs (vectorization
    # is pure computation with no shared state between families; each
    # family only writes its own packs/<slug>, details/<slug>.json, etc.,
    # so there's no cross-family interference).
    done: dict[str, tuple[dict, dict, int, list[str], str | None]] = {}
    for slug, entry, payload, n_variants, warns, err in _run_rebuilds(
            pending, site_data, downloads_dir, charsets, ucd, han_ref):
        done[slug] = (entry, payload, n_variants, warns, err)
        if err:
            print(f"  {slug}: FAILED ({err})")
        else:
            print(f"  {slug}: built ({len(entry['variants'])} variants)")
    # Aggregation walks in directory order so warning order and output
    # assembly are both deterministic.
    for slug, family_dir, facts in pending:
        entry, payload, n_variants, warns, err = done[slug]
        report.warnings.extend(warns)
        if err:
            report.warnings.append(f"{slug}: 构建失败,已跳过 — {err}")
            report.failed += 1
            continue
        report.variants += n_variants
        payload["facts"] = facts
        cache.store(slug, payload)
        entries.append(entry)
        all_downloads.extend(payload["downloads"])
        runs_by_slug[slug] = [tuple(r) for r in payload["runs"]]
        report.families += 1

    entries.sort(key=lambda e: e["slug"])
    _json_dump(
        {
            "schemaVersion": DATA_SCHEMA_VERSION,
            "generatedAt": "",
            "charsetIds": [c.id for c in charsets],
            "charsetNames": {
                c.id: {"zh": c.name_zh, "en": c.name_en or c.name_zh,
                       "section": c.section, "total": len(c.cps)}
                for c in charsets
            },
            "families": entries,
        },
        site_data / "index.json",
    )
    _json_dump({"entries": all_downloads}, downloads_dir / "manifest.json")

    from opf.emit import write_charsets_json, write_intervals

    write_intervals(runs_by_slug, site_data / "coverage-intervals.bin.gz")
    write_charsets_json(charsets, site_data / "charsets.json")

    # In --family mode, entries only contains cache-hit families (possibly
    # none, if the cache is entirely invalid), so treating it as "the
    # complete set of existing families" for cleanup would wrongly delete
    # other families' outputs.
    if not only_family:
        _prune_orphans(site_data, downloads_dir, {e["slug"] for e in entries},
                       {e["file"] for e in all_downloads})

    report.data_bytes = sum(p.stat().st_size for p in site_data.rglob("*") if p.is_file())
    report.took_s = time.monotonic() - t0
    return report


def _prune_orphans(site_data: Path, downloads_dir: Path, slugs: set[str],
                   download_files: set[str]) -> None:
    """Remove outputs that no longer belong to any existing family (after a family is renamed or deleted)."""
    import shutil

    for sub, is_dir in (("details", False), ("previews", True), ("og", False),
                        ("licenses", False), ("packs", True)):
        base = site_data / sub
        if not base.exists():
            continue
        for p in base.iterdir():
            slug = p.name if is_dir else p.stem
            if slug in slugs:
                continue
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
    keep = download_files | {"manifest.json"}
    for p in downloads_dir.iterdir():
        if p.is_file() and p.name not in keep:
            p.unlink()


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
    if report.failed:
        print(f"ERROR: {report.failed} 个家族构建失败(见 warn 行)", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
