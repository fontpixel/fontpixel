"""构建编排器：fonts/ → site/public/data + dist-downloads（契约 C5/C6/C8）。

用法：python -m opf.build --fonts fonts --out site/public/data \
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
    """家族层面取各变体里最好的那一档。

    家族的 scripts 是各变体的并集,小尺寸覆盖不全、大尺寸达标的字体
    (如方舟像素)会同时出现 zh-hans 和 zh-hans-partial,两个标签并列
    对读者没有意义。
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
    """返回 (index_entry, cache_payload)。"""
    slug = family_dir.name
    meta = load_family_meta(family_dir)
    files = _font_files(family_dir)

    # 上游偶尔混进残文件（只有一两个字形的占位），排除掉
    if meta.exclude:
        import fnmatch
        files = [
            p for p in files
            if not any(fnmatch.fnmatch(p.name, pat) for pat in meta.exclude)
        ]
    # 上游常把同一字面拆成几份（拉丁一份、汉字一份），分别收录会显示成几个
    # 残缺字体，合并回一个变体。按名字自动归组，家族也可显式指定分组。
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

    # 先把每个字面解析好（该合并的合并），合不进去的仍单列成变体，
    # 否则那些字形就凭空消失了
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
        # 一个字形都没剩,说明该字面的字符集没解开(如 Adobe FontSpecific 这类
        # 自有编码),不是「覆盖率低」而是根本没解析出来。让整族构建失败,
        # 由上层的单家族隔离记进报告——绝不能把空字体发布到站上。
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
        # 纯 CJK 字库（KS X 1001、JIS 等编码）常一个 ASCII 都没有，装上后
        # 拉丁字母和空格会掉到别的字体。这不是错误，但用户该被告知。
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
    # 变体按尺寸排序，页面上的切换器才不会是 13、15、16、14、12 这种文件名序
    _WEIGHT = {"light": 0, "regular": 1, "bold": 2}
    built.sort(key=lambda b: (b.desc.size, _WEIGHT.get(b.desc.weight, 9),
                              b.desc.spacing, b.desc.script_subset or ""))

    license_info = detect_license(family_dir, [b.font for b in built],
                                  meta.license_override)
    _cps_cache = {b.desc.id: font_cps(b.font) for b in built}

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
    scripts = merge_scripts(scripts)
    sample_lang = meta.sample_lang or pick_sample_lang(best.coverage)
    sample_text = meta.samples.get(sample_lang) or SAMPLES.get(sample_lang, SAMPLES["latin"])
    # 图标／符号字体排不出任何一句预设样例，改用它自己的字形
    if not meta.samples.get(sample_lang):
        best_cps = font_cps(best.font)
        if sample_is_broken(sample_text, best_cps):
            sample_text = specimen(best_cps) or sample_text

    # 资产
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
    # 逐变体的墨迹高度：汉字墨迹字面高，没有汉字就退回大写字高。
    # 只下发家族最大值的话，按「14-14」筛选就搜不到有 14 档变体的家族。
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
        # 全部字表的家族级覆盖率（取各变体最大值），顺序对齐 index.charsetIds
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
        # 样例文本必须随索引一起下发：图标字体用的是自身字形，
        # 前端按 sampleLang 查表只会查回一句排不出来的英文
        "sampleText": sample_text,
        # 顶部预览用的是字形最多的那个变体；输入框要跟它一致，
        # 否则上下两处显示的是同一字体的不同尺寸
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
    """家族 zip 里的来源 README。重建与元数据快路径共用同一份定义。"""
    return (f"{meta.name}\n来源：{meta.provenance or meta.homepage or '-'}\n"
            f"许可证：{license_name}\n由 开源像素字体馆 打包\n")


def _copyright_line(meta, license_name: str) -> str:
    """写进 TTF name 表的版权行。重建与元数据快路径共用同一份定义。"""
    return (f"{meta.name} — {license_name}"
            + (f"（{'、'.join(meta.authors)}）" if meta.authors else ""))



def _describe(meta, slug: str) -> dict:
    """index 条目里纯粹来自 family.toml 的展示字段。

    这是「什么算描述性」的唯一定义：重建路径靠它拼 entry，命中缓存的快路径
    靠它回填。新增字段写进这里，两条路径就不会跑偏；没写进来的字段按构造
    属于结构性，改了会照常触发重建（见 cache._STRUCTURAL_KEYS）。
    """
    return {
        "slug": slug,
        "name": meta.name,
        # 各语言写法都下发，取哪个由站点按界面语言决定（i18n/pickName）
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
    """详情页里纯粹来自 family.toml 的展示字段。"""
    return {
        "homepage": meta.homepage,
        "repository": meta.repository,
        "description": meta.description,
        "descriptionEn": meta.description_en or meta.description,
        "provenance": meta.provenance,
        "provenanceEn": meta.provenance_en or meta.provenance,
    }


def _search_text_for(meta, slug: str) -> str:
    """家族的可搜索文本。简繁展开后，搜「东云」也能命中「東雲」。

    name_en/author_en 是英文页面上显示的那一份，不收进来就搜不到；
    aliases 是曾用名与别名（见 family.toml）。
    """
    return search_text(meta.name, *family_names(meta).values(),
                       " ".join(meta.authors), " ".join(meta.authors_en), slug,
                       " ".join(meta.vibes), " ".join(meta.aliases))


def _refresh_metadata(
    slug: str, family_dir: Path, site_data: Path, downloads_dir: Path,
    cached: dict,
) -> tuple[dict, list[dict]] | None:
    """字形产物没变、只有 family.toml 的展示字段变了时走的路径。

    缓存(见 cache.facts_match)只认字体文件与 family.toml 的结构性字段，
    所以命中之后 index 条目、详情页与下载物里的文本可能还是旧的——这里把
    它们刷新一遍，代价是几毫秒，而不是把 131 个家族重新矢量化半小时。

    返回 None 表示刷不动(产物缺失)，交给上游走全量重建。
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


# 并行重建的共享上下文。fork 出的子进程直接继承（零拷贝），不走 pickle——
# charsets/ucd 有几十 MB，逐任务序列化就把并行的收益吃掉了。
_POOL_CTX: dict = {}


def _rebuild_one(args: tuple[str, str]) -> tuple[str, dict | None, dict | None,
                                                 int, list[str], str | None]:
    """在工作进程里构建一个家族。返回 (slug, entry, payload, 变体数, warnings, 错误)。"""
    slug, family_dir = args
    ctx = _POOL_CTX
    local = BuildReport()          # 子进程攒自己的 warnings，回主进程再合并
    try:
        entry, payload = _build_family(
            Path(family_dir), ctx["site_data"], ctx["downloads_dir"],
            ctx["charsets"], ctx["ucd"], ctx["han_ref"], local,
        )
    except Exception as e:  # noqa: BLE001 - 单家族失败不拖垮全站构建
        return slug, None, None, 0, local.warnings, str(e)
    return slug, entry, payload, local.variants, local.warnings, None


def _jobs() -> int:
    """并行度：OPF_JOBS 覆盖，默认不超过 8——最大的几个家族（unifont、mona）
    在 TTF 导出时各要吃 1~2GB 内存，并行度太高会先撞内存而不是 CPU。"""
    env = os.environ.get("OPF_JOBS", "").strip()
    if env:
        return max(1, int(env))
    return max(1, min(os.cpu_count() or 1, 8))


def _run_rebuilds(pending, site_data, downloads_dir, charsets, ucd, han_ref):
    """把待重建的家族分发到进程池；起不了 fork 或只有一个任务就串行。"""
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
        mp_ctx = mp.get_context("fork")   # 显式 fork：Python 3.14 起默认不再是它
    except ValueError:
        for a in args:
            yield _rebuild_one(a)
        return

    # 大家族先进队（按目录体积估算）：unifont 这类不能压到队尾拖长收尾
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
            load_family_meta(family_dir)  # 物化 stub，保证缓存键稳定
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

    # 需要重建的家族按 CPU 并行跑（矢量化是纯计算，互相不共享任何状态；
    # 每个家族只写自己的 packs/<slug>、details/<slug>.json 等，互不踩踏）
    done: dict[str, tuple[dict, dict, int, list[str], str | None]] = {}
    for slug, entry, payload, n_variants, warns, err in _run_rebuilds(
            pending, site_data, downloads_dir, charsets, ucd, han_ref):
        done[slug] = (entry, payload, n_variants, warns, err)
        if err:
            print(f"  {slug}: FAILED ({err})")
        else:
            print(f"  {slug}: built ({len(entry['variants'])} variants)")
    # 汇总按目录序走，保证 warnings 顺序与产物拼装都是确定的
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

    # --family 模式下 entries 只含命中缓存的家族（缓存整体失效时可能一个都没有），
    # 拿它当「现存家族全集」去清理，会把其他家族的产物误删
    if not only_family:
        _prune_orphans(site_data, downloads_dir, {e["slug"] for e in entries},
                       {e["file"] for e in all_downloads})

    report.data_bytes = sum(p.stat().st_size for p in site_data.rglob("*") if p.is_file())
    report.took_s = time.monotonic() - t0
    return report


def _prune_orphans(site_data: Path, downloads_dir: Path, slugs: set[str],
                   download_files: set[str]) -> None:
    """移除不再属于任何现存家族的产物(家族改名/删除后)。"""
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
