"""许可证识别：特征短语指纹 + 三级置信(spec §4.4)。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from fbf.model import ParsedFont


@dataclass
class LicenseInfo:
    spdx: str | None
    name: str
    file: str | None
    commercial: bool | None
    confidence: str  # auto-high | auto-low | manual | unknown
    note: str = ""


COMMERCIAL_OK = {
    "OFL-1.1", "OFL-1.0", "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause",
    "CC0-1.0", "Unlicense", "WTFPL", "CC-BY-4.0", "CC-BY-SA-4.0", "IPA-1.0",
    "GPL-2.0-with-font-exception", "GPL-3.0-with-font-exception",
    "LicenseRef-Mplus", "LicenseRef-PublicDomain",
}

_NAMES = {
    "OFL-1.1": "SIL Open Font License 1.1",
    "OFL-1.0": "SIL Open Font License 1.0",
    "MIT": "MIT License",
    "Apache-2.0": "Apache License 2.0",
    "BSD-2-Clause": "BSD 2-Clause License",
    "BSD-3-Clause": "BSD 3-Clause License",
    "GPL-2.0-only": "GNU GPL v2",
    "GPL-3.0-only": "GNU GPL v3",
    "GPL-2.0-with-font-exception": "GNU GPL v2 with Font Exception",
    "GPL-3.0-with-font-exception": "GNU GPL v3 with Font Exception",
    "LGPL-2.1-only": "GNU LGPL v2.1",
    "CC0-1.0": "CC0 1.0 公有领域贡献",
    "CC-BY-4.0": "CC Attribution 4.0",
    "CC-BY-SA-4.0": "CC Attribution-ShareAlike 4.0",
    "WTFPL": "WTFPL",
    "Unlicense": "The Unlicense",
    "IPA-1.0": "IPA Font License 1.0",
    "LicenseRef-Mplus": "M+ Fonts License",
    "LicenseRef-Baekmuk": "Baekmuk License",
    "LicenseRef-PublicDomain": "Public Domain",
}

_FILE_PATTERNS = ("license", "licence", "copying", "ofl", "copyright", "unlicense")
_MAX_LICENSE_BYTES = 300_000


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _classify_text(norm: str) -> str | None:
    """归一化文本 → SPDX id；按特异性从高到低匹配。"""
    if "sil open font license" in norm or "scripts.sil.org/ofl" in norm:
        if "version 1.0" in norm and "version 1.1" not in norm:
            return "OFL-1.0"
        return "OFL-1.1"
    if "ipa font license agreement v1.0" in norm:
        return "IPA-1.0"
    if "do what the fuck you want" in norm:
        return "WTFPL"
    if "this is free and unencumbered software" in norm:
        return "Unlicense"
    if "attribution-sharealike 4.0" in norm:
        return "CC-BY-SA-4.0"
    if "attribution 4.0 international" in norm:
        return "CC-BY-4.0"
    if "cc0 1.0" in norm or ("public domain dedication" in norm and "creative commons" in norm):
        return "CC0-1.0"
    if "apache license" in norm and "version 2.0" in norm:
        return "Apache-2.0"
    if "lesser general public license" in norm[:300]:
        return "LGPL-2.1-only"
    if "gnu general public license" in norm:
        fe = "font exception" in norm or "embed this font" in norm
        v3 = "version 3" in norm[:300]
        if fe:
            return "GPL-3.0-with-font-exception" if v3 else "GPL-2.0-with-font-exception"
        return "GPL-3.0-only" if v3 else "GPL-2.0-only"
    if "redistributions of source code must retain" in norm:
        return "BSD-3-Clause" if "neither the name" in norm else "BSD-2-Clause"
    if "permission is hereby granted, free of charge" in norm and (
        "to deal in the software without restriction" in norm
        or "mit license" in norm
    ):
        return "MIT"
    if "m+ fonts project" in norm or (
        "these fonts are free software" in norm and "unlimited permission" in norm
    ):
        return "LicenseRef-Mplus"
    if "baekmuk" in norm and "kim" in norm:
        return "LicenseRef-Baekmuk"
    return None


def _hint_from_props(fonts: list[ParsedFont]) -> str | None:
    blob = " ".join(
        str(f.props.get(k, ""))
        for f in fonts
        for k in ("COPYRIGHT", "NOTICE", "LICENSE")
    )
    norm = _normalize(blob)
    if not norm:
        return None
    if "sil open font license" in norm or "ofl" in norm.split():
        return "OFL-1.1"
    if "public domain" in norm:
        return "LicenseRef-PublicDomain"
    if "gnu general public license" in norm or re.search(r"\bgpl\b", norm):
        return "GPL-2.0-only"
    if "creative commons" in norm:
        return "CC-BY-4.0"
    return None


def _commercial(spdx: str | None) -> bool | None:
    if spdx is None:
        return None
    return True if spdx in COMMERCIAL_OK else None


# 多许可并存时的偏好序（字体本体许可优先于代码许可）
_PREFERENCE = [
    "OFL-1.1", "OFL-1.0", "IPA-1.0", "LicenseRef-Mplus", "LicenseRef-Baekmuk",
    "CC-BY-SA-4.0", "CC-BY-4.0", "CC0-1.0", "Unlicense", "WTFPL",
    "GPL-2.0-with-font-exception", "GPL-3.0-with-font-exception",
    "GPL-2.0-only", "GPL-3.0-only", "LGPL-2.1-only",
    "Apache-2.0", "BSD-3-Clause", "BSD-2-Clause", "MIT",
    "LicenseRef-PublicDomain",
]


def detect_license(
    family_dir: Path, fonts: list[ParsedFont], toml_override: dict | None
) -> LicenseInfo:
    if toml_override:
        spdx = toml_override.get("spdx")
        return LicenseInfo(
            spdx=spdx,
            name=toml_override.get("name") or _NAMES.get(spdx or "", spdx or ""),
            file=toml_override.get("file"),
            commercial=toml_override.get("commercial", _commercial(spdx)),
            confidence="manual",
            note=toml_override.get("note", ""),
        )

    found: dict[str, str] = {}  # spdx -> file name
    for p in sorted(family_dir.iterdir()) if family_dir.exists() else []:
        if not p.is_file() or p.stat().st_size > _MAX_LICENSE_BYTES:
            continue
        lname = p.name.lower()
        if not (
            any(pat in lname for pat in _FILE_PATTERNS)
            or lname.endswith((".txt", ".md"))
        ):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        spdx = _classify_text(_normalize(text))
        if spdx and spdx not in found:
            found[spdx] = p.name

    if found:
        ranked = sorted(found, key=lambda s: _PREFERENCE.index(s) if s in _PREFERENCE else 99)
        best = ranked[0]
        note = ""
        if len(ranked) > 1:
            others = ", ".join(_NAMES.get(s, s) for s in ranked[1:])
            note = f"目录中另含 {others}（通常适用于构建代码或部分文件）"
        return LicenseInfo(
            spdx=best,
            name=_NAMES.get(best, best),
            file=found[best],
            commercial=_commercial(best),
            confidence="auto-high",
            note=note,
        )

    hint = _hint_from_props(fonts)
    if hint:
        return LicenseInfo(
            spdx=hint,
            name=_NAMES.get(hint, hint),
            file=None,
            commercial=_commercial(hint),
            confidence="auto-low",
            note="仅依据字体内嵌属性推断，待确认",
        )

    return LicenseInfo(
        spdx=None, name="未识别", file=None, commercial=None, confidence="unknown"
    )
