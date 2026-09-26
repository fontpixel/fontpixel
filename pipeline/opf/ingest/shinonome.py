"""Shinonome font (東雲フォント) source → merged Unicode BDF.

Upstream code4fukui/shinonome-font distributes fonts as `.bit` (an ASCII
pixel-art rendition of BDF), split into multiple directories by charset, with
derived glyphs expressed as diffs:

    latin1/font_src.bit           ISO 8859-1 base
    hankaku/font_src_diff.bit     JIS X 0201, diff over latin1
    kanjic/font_src.bit           JIS X 0208 base (Gothic)
    mincho/font_src_diff.bit      Mincho, diff over kanjic
    marumoji/font_src_diff.bit    Marumoji, diff over kanjic (12px only)

This module calls upstream's bundled public-domain Perl tools
(tools/bit2bdf, tools/bdfmerge) to reconstruct the BDF for each charset, then
merges them into a single Unicode BDF per these rules:

    latin1   -> take all (ISO 8859-1 to Unicode is a standard mapping, and 0x5C is backslash)
    hankaku  -> only take halfwidth katakana U+FF61-FF9F (its ASCII range maps 0x5C to yen sign, so skip it)
    kanji    -> take all

License: the Shinonome font license declares all data Public Domain (the
author waives rights under Japanese law).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from opf.model import ParsedFont
from opf.parsers.bdf import parse_bdf

HALFWIDTH_KANA = range(0xFF61, 0xFFA0)

STYLES = {
    "gothic": ("kanjic", "東雲ゴシック", "Shinonome Gothic"),
    "mincho": ("mincho", "東雲明朝", "Shinonome Mincho"),
    "marumoji": ("marumoji", "東雲丸文字", "Shinonome Marumoji"),
}


def _tools(repo: Path, work: Path) -> tuple[Path, Path]:
    """Replace the @PERL@ placeholder in tools/*.in with the real interpreter."""
    if shutil.which("perl") is None:
        raise RuntimeError("perl is required to run upstream's bit2bdf / bdfmerge")
    out = []
    for name in ("bit2bdf", "bdfmerge"):
        src = repo / "tools" / f"{name}.in"
        dst = work / name
        dst.write_text(
            src.read_text(encoding="utf-8").replace("#!@PERL@", "#!/usr/bin/perl", 1),
            encoding="utf-8",
        )
        dst.chmod(0o755)
        out.append(dst)
    return out[0], out[1]


def _run(cmd: list[str], stdout: Path) -> None:
    with stdout.open("wb") as fh:
        r = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr.decode('utf-8', 'replace')[:300]}")


def _to_bdf(bit2bdf: Path, bdfmerge: Path, work: Path, name: str,
            base: Path, diff: Path | None) -> Path:
    """(optional merge) + bit2bdf → BDF path."""
    src = base
    if diff is not None:
        merged = work / f"{name}.bit"
        _run([str(bdfmerge), str(diff), str(base)], merged)
        src = merged
    bdf = work / f"{name}.bdf"
    _run([str(bit2bdf), str(src)], bdf)
    # upstream's header contains autoconf placeholders; replace them with real values so they don't pollute the property table
    text = bdf.read_text(encoding="latin-1")
    text = text.replace("@FOUNDRY@", "efont").replace("@FAMILY@", "Shinonome")
    bdf.write_text(text, encoding="latin-1")
    return bdf


def build(repo: Path, size: int, style: str, work: Path) -> ParsedFont | None:
    """Build a merged Unicode font for a given size and style; returns None if that combination doesn't exist."""
    kanji_dir, name_zh, name_en = STYLES[style]
    sd = repo / str(size)
    if not sd.is_dir():
        return None

    latin_base = sd / "latin1" / "font_src.bit"
    hankaku_diff = sd / "hankaku" / "font_src_diff.bit"
    kanji_base = sd / "kanjic" / "font_src.bit"
    style_diff = sd / kanji_dir / "font_src_diff.bit"
    if not latin_base.exists():
        return None
    if style != "gothic" and not style_diff.exists():
        return None
    if style == "gothic" and not kanji_base.exists() and size != 18:
        return None

    bit2bdf, bdfmerge = _tools(repo, work)
    tag = f"{style}{size}"
    parts: list[tuple[ParsedFont, str]] = []

    latin = parse_bdf(_to_bdf(bit2bdf, bdfmerge, work, f"{tag}-latin",
                              latin_base, None), "shinonome")
    parts.append((latin, "latin"))

    if hankaku_diff.exists():
        han = parse_bdf(_to_bdf(bit2bdf, bdfmerge, work, f"{tag}-hankaku",
                                latin_base, hankaku_diff), "shinonome")
        parts.append((han, "hankaku"))

    if kanji_base.exists():
        if style == "gothic":
            kanji = parse_bdf(_to_bdf(bit2bdf, bdfmerge, work, f"{tag}-kanji",
                                      kanji_base, None), "shinonome")
        else:
            kanji = parse_bdf(_to_bdf(bit2bdf, bdfmerge, work, f"{tag}-kanji",
                                      kanji_base, style_diff), "shinonome")
        parts.append((kanji, "kanji"))
    elif style != "gothic":
        return None  # no kanji base for this size, so Mincho/Marumoji can't be derived

    glyphs: dict[int, object] = {}
    warnings: list[str] = []
    for font, kind in parts:
        for g in font.glyphs:
            if kind == "hankaku" and g.cp not in HALFWIDTH_KANA:
                continue  # per JIS convention its ASCII range renders 0x5C as yen sign, so skip it
            if g.cp in glyphs:
                continue
            glyphs[g.cp] = g
        warnings.extend(w for w in font.warnings if "unmappable" not in w)

    if not glyphs:
        return None
    ref = parts[-1][0]
    vals = list(glyphs.values())
    xoff = min(g.bbx for g in vals)
    yoff = min(g.bby for g in vals)
    bw = max(g.bbx + g.bbw for g in vals) - xoff
    bh = max(g.bby + g.bbh for g in vals) - yoff
    return ParsedFont(
        path=repo,
        family_slug=f"shinonome-{style}",
        file_name=f"shinonome-{style}-{size}px.bdf",
        props={
            "FONT": (f"-efont-{name_en}-Medium-R-Normal--{size}-"
                     f"{size * 10}-75-75-P-{size * 10}-ISO10646-1"),
            "FOUNDRY": "efont",
            "FAMILY_NAME": name_en,
            "WEIGHT_NAME": "Medium",
            "SLANT": "R",
            "SETWIDTH_NAME": "Normal",
            "PIXEL_SIZE": size,
            "POINT_SIZE": size * 10,
            "RESOLUTION_X": 75,
            "RESOLUTION_Y": 75,
            "SPACING": "P",
            "CHARSET_REGISTRY": "ISO10646",
            "CHARSET_ENCODING": "1",
            "COPYRIGHT": "Public Domain",
            "NOTICE": ("Shinonome font, The Electronic Font Open Laboratory. "
                       "Public Domain. Rebuilt to Unicode BDF by "
                       "FontPixel.com."),
        },
        pixel_size=size,
        ascent=ref.ascent,
        descent=ref.descent,
        bbox=(bw, bh, xoff, yoff),
        glyphs=[glyphs[cp] for cp in sorted(glyphs)],
        warnings=sorted(set(warnings)),
    )


def build_all(repo: Path, dest_root: Path) -> dict[str, list[tuple[int, int]]]:
    """Build every style and size, writing into dest_root/shinonome-<style>/.

    Returns {slug: [(size, glyph_count), ...]}.
    """
    from opf.ingest.bdfwrite import write_bdf

    made: dict[str, list[tuple[int, int]]] = {}
    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        for style in STYLES:
            for size in (12, 14, 16, 18):
                font = build(repo, size, style, work)
                if font is None:
                    continue
                slug = f"shinonome-{style}"
                out = dest_root / slug
                out.mkdir(parents=True, exist_ok=True)
                write_bdf(font, out / font.file_name)
                made.setdefault(slug, []).append((size, len(font.glyphs)))
    return made


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Shinonome fonts → Unicode BDF")
    ap.add_argument("--repo", type=Path, required=True, help="root of the shinonome-font repository")
    ap.add_argument("--dest", type=Path, required=True, help="the fonts/ directory")
    args = ap.parse_args()
    for slug, items in sorted(build_all(args.repo, args.dest).items()):
        for size, n in items:
            print(f"{slug}: {size}px → {n} glyphs")


if __name__ == "__main__":
    main()
