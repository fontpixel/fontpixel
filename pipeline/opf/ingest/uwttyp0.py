"""UW ttyp0's font-specific encoding → Unicode BDF.

Upstream distributes a "fontspecific" master BDF (`CHARSET_REGISTRY "UW"`,
ENCODING is the font's internal ordinal, glyph names look like
`LtCapALdot`), and `genbdf` combines it with `mgl/*.mgl` mapping tables at
install time to generate the BDF for each encoding. This module reads
`mgl/unicode.mgl` directly (format: `PUT <glyph name> <code point>`) and
remaps the master BDF straight to Unicode BDF -- no need to run upstream's
autotools build.
"""

from __future__ import annotations

import re
from pathlib import Path

from opf.model import ParsedFont
from opf.parsers.bdf import parse_bdf

_PUT = re.compile(r"^PUT\s+(\S+)\s+0x([0-9A-Fa-f]+)\s*$")
_COPYTO = re.compile(r"^IFUNDEF\s+(\S+)\s+COPYTO\s+(\S+)\s+(\S+)\s*$")


def load_unicode_map(mgl: Path) -> dict[str, int]:
    """Glyph name → Unicode code point."""
    table: dict[str, int] = {}
    for line in mgl.read_text(encoding="latin-1").splitlines():
        line = line.strip()
        m = _PUT.match(line)
        if m:
            table.setdefault(m.group(1), int(m.group(2), 16))
    return table


def convert(bdf: Path, mgl: Path, family_slug: str) -> ParsedFont:
    """Remap a fontspecific master BDF to Unicode."""
    font = parse_bdf(bdf, family_slug, remap_charset=False)
    table = load_unicode_map(mgl)

    remapped: dict[int, object] = {}
    unmapped = 0
    for g in font.glyphs:
        cp = table.get(g.name)
        if cp is None:
            unmapped += 1
            continue
        if cp in remapped:
            continue
        g.cp = cp
        remapped[cp] = g

    if not remapped:
        raise ValueError(f"{bdf}: 没有字形能映射到 Unicode")

    vals = list(remapped.values())
    xoff = min(g.bbx for g in vals)
    yoff = min(g.bby for g in vals)
    bw = max(g.bbx + g.bbw for g in vals) - xoff
    bh = max(g.bby + g.bbh for g in vals) - yoff

    props = dict(font.props)
    props["CHARSET_REGISTRY"] = "ISO10646"
    props["CHARSET_ENCODING"] = "1"
    warnings = list(font.warnings)
    if unmapped:
        warnings.append(
            f"{unmapped} 个字形在 unicode.mgl 中无对应码位（多为控制符与行图形），已跳过"
        )

    font.props = props
    font.glyphs = [remapped[cp] for cp in sorted(remapped)]
    font.bbox = (bw, bh, xoff, yoff)
    font.warnings = warnings
    font.file_name = bdf.name
    return font


def build_all(repo: Path, dest: Path) -> list[tuple[str, int]]:
    """Convert repo/bdf/*.bdf, writing into dest; returns [(filename, glyph count), ...]."""
    from opf.ingest.bdfwrite import write_bdf

    mgl = repo / "mgl" / "unicode.mgl"
    if not mgl.exists():
        raise FileNotFoundError(f"缺少 {mgl}")
    dest.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, int]] = []
    for src in sorted((repo / "bdf").glob("*.bdf")):
        font = convert(src, mgl, dest.name)
        write_bdf(font, dest / src.name)
        out.append((src.name, len(font.glyphs)))
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="UW ttyp0 → Unicode BDF")
    ap.add_argument("--repo", type=Path, required=True, help="uw-ttyp0-x.y 解包目录")
    ap.add_argument("--dest", type=Path, required=True, help="fonts/uw-ttyp0 目录")
    args = ap.parse_args()
    for name, n in build_all(args.repo, args.dest):
        print(f"{name}: {n} 字形")


if __name__ == "__main__":
    main()
