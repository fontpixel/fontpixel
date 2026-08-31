"""把上游按字符集拆分的 BDF 合并回同一个字面。

X11 时代的日文字体常按字符集分发:`mplus_j10r.bdf` 只有汉字假名,
拉丁部分在 `mplus_j10r-iso-W5.bdf`,半角假名在 `mplus_j10r-jisx0201.bdf`。
它们是同一套设计的不同片段,分别收录会显示成几个残缺字体
(PixelMplus 的「完整版」里 ASCII 可见字符是 0/94,连空格都没有)。

归属规则:文件 B 是 A 的子集,当且仅当 B 的主干名等于 A 的主干名再接
一个 `-` 或 `_` 加后缀。存在多个候选时取最长的 A。
"""

from __future__ import annotations

from pathlib import Path

from opf.model import ParsedFont

_SUFFIXES = (".bdf.gz", ".pcf.gz", ".bdf", ".pcf")


def _stem(path: Path) -> str:
    name = path.name
    for s in _SUFFIXES:
        if name.lower().endswith(s):
            return name[: -len(s)]
    return path.stem


def group_files(paths: list[Path]) -> dict[Path, list[Path]]:
    """返回 {主文件: [子集文件, ...]}；没有子集的主文件对应空列表。"""
    stems = {p: _stem(p) for p in paths}
    parents: dict[Path, Path] = {}
    for b in paths:
        best: Path | None = None
        for a in paths:
            if a is b:
                continue
            sa, sb = stems[a], stems[b]
            if len(sb) > len(sa) and sb.startswith(sa) and sb[len(sa)] in "-_":
                if best is None or len(stems[a]) > len(stems[best]):
                    best = a
        if best is not None:
            parents[b] = best
    out: dict[Path, list[Path]] = {p: [] for p in paths if p not in parents}
    for child, parent in parents.items():
        # 父文件本身也可能是别人的子集，一路上溯到根
        while parent in parents:
            parent = parents[parent]
        out.setdefault(parent, []).append(child)
    for v in out.values():
        v.sort()
    return out


def merge(base: ParsedFont,
          extras: list[ParsedFont]) -> tuple[ParsedFont, list[str], list[ParsedFont]]:
    """把 extras 里 base 没有的码位补进 base。

    返回 (合并结果, 说明, 未能合并的字体)。未能合并的要由调用方保留成独立
    变体，否则那些字形就凭空消失了。

    只按像素尺寸判断能否合并：BDF 的字形自带相对基线的偏移，字面级的
    ascent/descent 不同不妨碍拼合，取各方最大值让所有字形都放得下即可。
    """
    notes: list[str] = []
    have = {g.cp for g in base.glyphs}
    added: list = []
    rejected: list[ParsedFont] = []
    for e in extras:
        if e.pixel_size != base.pixel_size:
            notes.append(
                f"{e.file_name}：像素尺寸与主文件不一致（{e.pixel_size}px vs "
                f"{base.pixel_size}px），未合并，单列为一个变体"
            )
            rejected.append(e)
            continue
        new = [g for g in e.glyphs if g.cp not in have]
        have.update(g.cp for g in new)
        added.extend(new)
        base.ascent = max(base.ascent, e.ascent)
        base.descent = max(base.descent, e.descent)
        notes.append(f"{e.file_name}：并入 {len(new)} 个字形")
    if not added:
        return base, notes, rejected

    base.glyphs = sorted(base.glyphs + added, key=lambda g: g.cp)
    xoff = min(g.bbx for g in base.glyphs)
    yoff = min(g.bby for g in base.glyphs)
    bw = max(g.bbx + g.bbw for g in base.glyphs) - xoff
    bh = max(g.bby + g.bbh for g in base.glyphs) - yoff
    base.bbox = (bw, bh, xoff, yoff)
    return base, notes, rejected
