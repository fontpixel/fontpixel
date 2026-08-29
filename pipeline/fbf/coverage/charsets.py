"""字表注册与加载(契约 C7)。

数据文件格式:头部 `# key: value` 注释(id/section/name_zh/name_en/
desc_zh/desc_en/source/license/order),正文每行:
`XXXX`(hex 码位)| `XXXX..YYYY`(闭区间)| 字面字符(逐字符取)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

_HEX_RE = re.compile(r"^[0-9A-Fa-f]{4,6}$")
_RANGE_RE = re.compile(r"^([0-9A-Fa-f]{4,6})\.\.([0-9A-Fa-f]{4,6})$")

SECTION_ORDER = ["gb", "prc-lit", "tw", "hk", "jp", "kr", "intl"]


@dataclass(frozen=True)
class Charset:
    id: str
    section: str
    name_zh: str
    name_en: str
    desc_zh: str
    desc_en: str
    cps: frozenset[int]
    source: str
    order: int = 999
    license: str = ""


def parse_charset_file(path: Path) -> Charset:
    meta: dict[str, str] = {}
    cps: set[int] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            body = line.lstrip("#").strip()
            key, sep, value = body.partition(":")
            if sep and key.strip() in {
                "id", "section", "name_zh", "name_en", "desc_zh",
                "desc_en", "source", "license", "order",
            }:
                meta[key.strip()] = value.strip()
            continue
        m = _RANGE_RE.match(line)
        if m:
            cps.update(range(int(m.group(1), 16), int(m.group(2), 16) + 1))
            continue
        if _HEX_RE.match(line):
            cps.add(int(line, 16))
            continue
        for ch in line:
            if not ch.isspace():
                cps.add(ord(ch))
    return Charset(
        id=meta.get("id", path.stem),
        section=meta.get("section", ""),
        name_zh=meta.get("name_zh", ""),
        name_en=meta.get("name_en", ""),
        desc_zh=meta.get("desc_zh", ""),
        desc_en=meta.get("desc_en", ""),
        cps=frozenset(cps),
        source=meta.get("source", ""),
        order=int(meta.get("order", "999")),
        license=meta.get("license", ""),
    )


def load_charsets(data_dir: Path = DATA_DIR) -> list[Charset]:
    out: list[Charset] = []
    for path in sorted(data_dir.rglob("*.txt")):
        if path.parent.name == "ucd":
            continue
        out.append(parse_charset_file(path))
    def key(c: Charset) -> tuple[int, int, str]:
        sec = SECTION_ORDER.index(c.section) if c.section in SECTION_ORDER else 99
        return (sec, c.order, c.id)
    return sorted(out, key=key)
