"""東雲フォント(Shinonome)源码 → 合并后的 Unicode BDF。

上游 code4fukui/shinonome-font 以 `.bit`(ASCII 点阵画版的 BDF)分发,
按字符集拆成多个目录,并用 diff 表达派生字形:

    latin1/font_src.bit           ISO 8859-1 基底
    hankaku/font_src_diff.bit     JIS X 0201,diff over latin1
    kanjic/font_src.bit           JIS X 0208 基底(ゴシック)
    mincho/font_src_diff.bit      明朝,diff over kanjic
    marumoji/font_src_diff.bit    丸文字,diff over kanjic(仅 12px)

本模块调用上游自带的公有领域 Perl 工具(tools/bit2bdf、tools/bdfmerge)
还原出各字符集的 BDF,再按下列规则合并成单个 Unicode BDF:

    latin1   → 全部收(ISO 8859-1 到 Unicode 是标准映射,且 0x5C 为反斜杠)
    hankaku  → 只收半角片假名 U+FF61–FF9F(其 ASCII 区 0x5C 为日元号,不取)
    kanji    → 全部收

授权:東雲フォントライセンス声明全部数据为 Public Domain(日本法下作者
声明不行使权利)。
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
    """把 tools/*.in 里的 @PERL@ 占位换成真实解释器。"""
    if shutil.which("perl") is None:
        raise RuntimeError("需要 perl 才能运行上游的 bit2bdf / bdfmerge")
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
        raise RuntimeError(f"{cmd[0]} 失败: {r.stderr.decode('utf-8', 'replace')[:300]}")


def _to_bdf(bit2bdf: Path, bdfmerge: Path, work: Path, name: str,
            base: Path, diff: Path | None) -> Path:
    """(可选 merge) + bit2bdf → BDF 路径。"""
    src = base
    if diff is not None:
        merged = work / f"{name}.bit"
        _run([str(bdfmerge), str(diff), str(base)], merged)
        src = merged
    bdf = work / f"{name}.bdf"
    _run([str(bit2bdf), str(src)], bdf)
    # 上游头部含 autoconf 占位符,替换成真实值以免污染属性表
    text = bdf.read_text(encoding="latin-1")
    text = text.replace("@FOUNDRY@", "efont").replace("@FAMILY@", "Shinonome")
    bdf.write_text(text, encoding="latin-1")
    return bdf


def build(repo: Path, size: int, style: str, work: Path) -> ParsedFont | None:
    """构建某尺寸某风格的合并 Unicode 字体;该组合不存在时返回 None。"""
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
        return None  # 该尺寸没有汉字基底,明朝/丸文字无从派生

    glyphs: dict[int, object] = {}
    warnings: list[str] = []
    for font, kind in parts:
        for g in font.glyphs:
            if kind == "hankaku" and g.cp not in HALFWIDTH_KANA:
                continue  # 其 ASCII 区按 JIS 习惯把 0x5C 画成日元号,不取
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
                       "Open Pixel Fonts."),
        },
        pixel_size=size,
        ascent=ref.ascent,
        descent=ref.descent,
        bbox=(bw, bh, xoff, yoff),
        glyphs=[glyphs[cp] for cp in sorted(glyphs)],
        warnings=sorted(set(warnings)),
    )


def build_all(repo: Path, dest_root: Path) -> dict[str, list[tuple[int, int]]]:
    """构建全部风格与尺寸,写入 dest_root/shinonome-<style>/。

    返回 {slug: [(size, glyph_count), ...]}。
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

    ap = argparse.ArgumentParser(description="東雲フォント → Unicode BDF")
    ap.add_argument("--repo", type=Path, required=True, help="shinonome-font 仓库根目录")
    ap.add_argument("--dest", type=Path, required=True, help="fonts/ 目录")
    args = ap.parse_args()
    for slug, items in sorted(build_all(args.repo, args.dest).items()):
        for size, n in items:
            print(f"{slug}: {size}px → {n} 字形")


if __name__ == "__main__":
    main()
