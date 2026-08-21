"""family.toml 读取与变体描述解析(spec §3.1/§3.2)。"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from pfc.metrics import is_monospaced
from pfc.model import ParsedFont

FORMS = {
    "gothic", "mingcho", "rounded", "kai", "fangsong", "serif-pixel", "sans",
    "script", "decorative", "terminal", "other", "",
}

_STUB = """\
# 此文件由构建器自动生成,请补全后把 TODO 注释删掉。
# form 可选值: gothic(黑体) | mingcho(宋体/明朝) | rounded(圆体) | kai(楷体)
#   | fangsong(仿宋) | serif-pixel(西文衬线) | sans(西文无衬线) | script(手写)
#   | decorative(装饰) | terminal(终端) | other
name = "{name}"
name_zh = ""            # TODO: 中文名(可留空)
author = ""             # TODO
homepage = ""           # TODO
repository = ""
description = ""        # TODO: 一句话介绍
form = ""               # TODO: 字形分类
vibes = []              # TODO: 气质标签,如 ["retro-game", "cute"]
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
    script_subset: str | None
    display: str


@dataclass
class FamilyMeta:
    slug: str
    name: str
    name_zh: str = ""
    author: str = ""
    homepage: str = ""
    repository: str = ""
    description: str = ""
    form: str = ""
    vibes: list[str] = field(default_factory=list)
    converted_from: str = ""
    provenance: str = ""
    curated: bool = True
    license_override: dict | None = None
    samples: dict[str, str] = field(default_factory=dict)
    variant_overrides: dict[str, dict] = field(default_factory=dict)


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
        author=str(data.get("author", "")),
        homepage=str(data.get("homepage", "")),
        repository=str(data.get("repository", "")),
        description=str(data.get("description", "")),
        form=str(data.get("form", "")),
        vibes=[str(v) for v in data.get("vibes", [])],
        converted_from=str(data.get("converted_from", "")),
        provenance=str(data.get("provenance", "")),
        curated=curated,
        license_override=data.get("license"),
        samples={str(k): str(v) for k, v in data.get("samples", {}).items()},
        variant_overrides={str(k): dict(v) for k, v in data.get("variants", {}).items()},
    )


_SCRIPT_TOKENS = {
    "zh_hans": "zh-Hans", "zh-hans": "zh-Hans", "sc": "zh-Hans", "cn": "zh-Hans",
    "zh_hant": "zh-Hant", "zh-hant": "zh-Hant", "tc": "zh-Hant", "tw": "zh-Hant",
    "ja": "ja", "jp": "ja", "ko": "ko", "kr": "ko", "latin": "latin",
}


def _sanitize_id(stem: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "-", stem)


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
        script_subset=ov.get("script_subset", script) or None,
        display=str(ov.get("display", stem)),
    )
