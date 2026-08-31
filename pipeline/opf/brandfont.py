"""Site-name web font: subset the characters used by the site name out of a
collection pixel font into a small font of its own.

The header site name used to be rendered page-by-page on canvas (pick a
glyph pack → rasterize → swap in the text), which flickered on every page
change. This now produces brand.woff2 at build time instead (a few KB,
cached once for the whole site), and the header goes back to plain text.
The single source of truth for the character list is
site/src/i18n/sitenames.json — the site's i18n and this script read the
same file, so a site-name change stays in sync on both sides.

The family is named FBF Brand rather than Fusion Pixel: OFL's Reserved
Font Name clause requires modified versions to be renamed, and this subset
counts as a modification.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from opf.parsers.bdf import parse_bdf
from opf.vectorize import build_vector_ttf

# Candidate sources, in preference order; use the first one that exists
# and fully covers the site name's character set.
# fusion-pixel's language variants share the same character set (only the
# CJK glyph shapes differ by language), so any one of them works.
SOURCES = (
    "fusion-pixel/fusion-pixel-12px-proportional-zh_hans.bdf",
    "unifont-ex/unifont-ex.bdf",   # fallback: covers everything, but the glyphs run larger
)


def build_brand_font(fonts_dir: Path, data_dir: Path, names_path: Path) -> dict:
    names = json.loads(names_path.read_text(encoding="utf-8"))
    cps = {ord(c) for text in names.values() for c in text if not c.isspace()}

    for rel in SOURCES:
        src = fonts_dir / rel
        if not src.exists():
            continue
        font = parse_bdf(src, src.parent.name)
        have = {g.cp for g in font.glyphs}
        if cps <= have:
            break
        missing = "".join(chr(c) for c in sorted(cps - have))
        print(f"  brandfont: {rel} 缺 {missing}，试下一个候选")
    else:
        raise SystemExit(f"brandfont: 没有候选字体能覆盖站名字符集")

    font.glyphs = [g for g in font.glyphs if g.cp in cps]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "brand.ttf"
        build_vector_ttf(
            font, "FBF Brand", "Regular", tmp, shape="square",
            copyright_=f"Subset of {src.parent.name} (OFL-1.1) for the site wordmark",
        )
        from fontTools.ttLib import TTFont

        f = TTFont(tmp, recalcTimestamp=False)
        try:
            f.flavor = "woff2"
            out_name = "brand.woff2"
            f.save(data_dir / out_name)
        except ImportError:            # fall back to woff when brotli isn't available (zlib always is)
            f.flavor = "woff"
            out_name = "brand.woff"
            f.save(data_dir / out_name)

    meta = {"file": out_name, "px": font.pixel_size, "family": "FBF Brand",
            "source": src.name, "glyphs": len(font.glyphs)}
    (data_dir / "brand.json").write_text(
        json.dumps(meta, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    size = (data_dir / out_name).stat().st_size
    print(f"  brandfont: {out_name} {size/1024:.1f}KB，{len(font.glyphs)} 字形，"
          f"源 {src.name}")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--names", type=Path, required=True)
    a = ap.parse_args()
    build_brand_font(a.fonts, a.data, a.names)


if __name__ == "__main__":
    main()
