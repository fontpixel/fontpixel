"""family.toml 读取与变体描述解析(spec §3.1/§3.2)。"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from opf.metrics import is_monospaced
from opf.model import ParsedFont

FORMS = {
    "gothic", "mingcho", "rounded", "kai", "fangsong", "serif-pixel", "sans",
    "script", "decorative", "terminal", "other", "",
}

_STUB = """\
# 此文件由构建器自动生成，请补全后把 TODO 注释删掉。
# form 可选值：gothic（黑体） | mingcho（宋体/明朝） | rounded（圆体） | kai（楷体）
#   | fangsong（仿宋） | serif-pixel（西文衬线） | sans（西文无衬线） | script（手写）
#   | decorative（装饰） | terminal（终端） | other
name = "{name}"
name_zh = ""            # TODO: 中文名（可留空）
authors = []            # TODO: 作者，如 ["TakWolf"]
homepage = ""           # TODO
repository = ""
description = ""        # TODO: 一句话介绍
form = ""               # TODO: 字形分类
vibes = []              # TODO: 气质标签，如 ["retro-game", "cute"]
converted_from = ""
provenance = ""
"""


@dataclass
class VariantDesc:
    id: str
    file: str
    size: int
    weight: str
    spacing: str
    width: str
    """上游文档标注的推荐显示尺寸（px）；0 表示上游未说明。"""
    display_size: int
    script_subset: str | None
    display: str


@dataclass
class FamilyMeta:
    slug: str
    name: str
    name_zh: str = ""
    """并列作者，逐个渲染成按作者名搜索的链接，所以每项要干净、可搜索：
    「基于某某字体」这类说明写进 provenance，不要塞在名字里。"""
    authors: list[str] = field(default_factory=list)
    homepage: str = ""
    repository: str = ""
    description: str = ""
    form: str = ""
    vibes: list[str] = field(default_factory=list)
    """曾用名、上游项目名、原生语言名等——只进搜索文本，不在站上展示。"""
    aliases: list[str] = field(default_factory=list)
    converted_from: str = ""
    provenance: str = ""
    """各语言下的字体名，都是可选的；缺哪个就按 LOCALE_FALLBACK 往后退，
    最终落到 name。zh-Hant 缺省时由站点用 OpenCC 从 zh-Hans 转出。"""
    name_en: str = ""
    name_zh_hans: str = ""
    name_zh_hant: str = ""
    name_ja: str = ""
    name_ko: str = ""
    name_fr: str = ""
    authors_en: list[str] = field(default_factory=list)
    description_en: str = ""
    provenance_en: str = ""
    merge_subsets: bool = False
    merge: dict[str, list[str]] = field(default_factory=dict)
    exclude: list[str] = field(default_factory=list)
    curated: bool = True
    added: str = ""
    sample_lang: str = ""
    license_override: dict | None = None
    samples: dict[str, str] = field(default_factory=dict)
    variant_overrides: dict[str, dict] = field(default_factory=dict)


def _authors(data: dict, key: str, legacy_key: str) -> list[str]:
    """读作者列表；旧文件里的单值 author = "..." 当作单元素列表。"""
    if key in data:
        return [str(a).strip() for a in data[key] if str(a).strip()]
    one = str(data.get(legacy_key, "")).strip()
    return [one] if one else []


def family_names(meta: "FamilyMeta") -> dict[str, str]:
    """家族名的各语言写法，只收非空的。键用站点的 locale 标识。"""
    pairs = {
        "en": meta.name_en,
        "zh-Hans": meta.name_zh_hans,
        "zh-Hant": meta.name_zh_hant,
        "ja": meta.name_ja,
        "ko": meta.name_ko,
        "fr": meta.name_fr,
    }
    return {k: v for k, v in pairs.items() if v}


def _titleize(slug: str) -> str:
    return " ".join(w.capitalize() for w in re.split(r"[-_]+", slug) if w)


def load_family_meta(family_dir: Path) -> FamilyMeta:
    slug = family_dir.name
    toml_path = family_dir / "family.toml"
    if not toml_path.exists():
        toml_path.write_text(_STUB.format(name=_titleize(slug)), encoding="utf-8")
        return FamilyMeta(slug=slug, name=_titleize(slug), curated=False)

    data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    curated = "TODO" not in toml_path.read_text(encoding="utf-8")
    return FamilyMeta(
        slug=slug,
        name=str(data.get("name") or _titleize(slug)),
        name_zh=str(data.get("name_zh", "")),
        authors=_authors(data, "authors", "author"),
        homepage=str(data.get("homepage", "")),
        repository=str(data.get("repository", "")),
        description=str(data.get("description", "")),
        form=str(data.get("form", "")),
        vibes=[str(v) for v in data.get("vibes", [])],
        aliases=[str(a) for a in data.get("aliases", [])],
        converted_from=str(data.get("converted_from", "")),
        provenance=str(data.get("provenance", "")),
        name_en=str(data.get("name_en", "")),
        # name_zh 是加入多语言字段之前的旧写法，按简体读进来
        name_zh_hans=str(data.get("name_zh_hans", "") or data.get("name_zh", "")),
        name_zh_hant=str(data.get("name_zh_hant", "")),
        name_ja=str(data.get("name_ja", "")),
        name_ko=str(data.get("name_ko", "")),
        name_fr=str(data.get("name_fr", "")),
        authors_en=_authors(data, "authors_en", "author_en"),
        description_en=str(data.get("description_en", "")),
        provenance_en=str(data.get("provenance_en", "")),
        merge_subsets=bool(data.get("merge_subsets", False)),
        merge={str(k): [str(x) for x in v]
               for k, v in data.get("merge", {}).items()},
        exclude=[str(x) for x in data.get("exclude", [])],
        curated=curated,
        added=str(data.get("added", "")),
        sample_lang=str(data.get("sample_lang", "")),
        license_override=data.get("license"),
        samples={str(k): str(v) for k, v in data.get("samples", {}).items()},
        variant_overrides={str(k): dict(v) for k, v in data.get("variants", {}).items()},
    )


_SCRIPT_TOKENS = {
    "zh_hans": "zh-Hans", "zh-hans": "zh-Hans", "sc": "zh-Hans", "cn": "zh-Hans",
    "zh_hant": "zh-Hant", "zh-hant": "zh-Hant", "tc": "zh-Hant", "tw": "zh-Hant",
    "hk": "zh-Hant", "tr": "zh-Hant",  # zh_hk 港标字形 / zh_tr 传承字形
    "ja": "ja", "jp": "ja", "ko": "ko", "kr": "ko", "latin": "latin",
}


def _sanitize_id(stem: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", stem)


_WIDTH_TOKENS = {
    "semicondensed": "semicondensed",
    "semiexpanded": "semiexpanded",
    "condensed": "condensed",
    "narrow": "condensed",
    "expanded": "expanded",
    "extended": "expanded",
    "wide": "expanded",
}


def resolve_variant(f: ParsedFont, meta: FamilyMeta) -> VariantDesc:
    stem = re.sub(r"\.(bdf|pcf)(\.gz)?$", "", f.file_name, flags=re.I)
    lower = stem.lower()
    tokens = [t for t in re.split(r"[-_.]+", lower) if t]

    weight = "regular"
    wn = str(f.props.get("WEIGHT_NAME", "")).lower()
    if "bold" in wn or "bold" in tokens or re.search(r"\d+b$", lower):
        weight = "bold"
    elif "light" in wn or "light" in tokens:
        weight = "light"

    # 字宽：Condensed 这类与常规同尺寸同字重，不区分就会撞标签
    # （Galmuri11 与 Galmuri11-Condensed 都是「16px·常规·比例」）。
    # 只认真正表示字宽的词——有的工具把字重也写进 SETWIDTH 字段。
    width = "normal"
    sw = str(f.props.get("SETWIDTH_NAME", "")).lower().replace(" ", "")
    for token, val in _WIDTH_TOKENS.items():
        if token in sw or token in tokens or (len(token) > 4 and token in lower):
            width = val
            break

    spacing = ""
    sp = str(f.props.get("SPACING", "")).upper()
    if sp in {"C", "M"}:
        spacing = "monospaced"
    elif sp == "P":
        spacing = "proportional"
    if not spacing and ("monospaced" in tokens or "mono" in tokens):
        spacing = "monospaced"
    if not spacing:
        spacing = "monospaced" if is_monospaced(f) else "proportional"

    script: str | None = None
    joined = lower
    for tok, val in _SCRIPT_TOKENS.items():
        if tok in tokens or (len(tok) > 2 and tok in joined):
            script = val
            break

    ov = meta.variant_overrides.get(f.file_name, {})
    return VariantDesc(
        id=_sanitize_id(stem),
        file=f.file_name,
        size=int(ov.get("size", f.pixel_size)),
        weight=str(ov.get("weight", weight)),
        spacing=str(ov.get("spacing", spacing)),
        width=str(ov.get("width", width)),
        display_size=int(ov.get("display_size", 0)),
        script_subset=ov.get("script_subset", script) or None,
        display=str(ov.get("display", stem)),
    )
