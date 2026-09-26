"""Merge BDFs that upstream split by charset back into a single typeface.

Japanese fonts from the X11 era were often distributed split by charset:
`mplus_j10r.bdf` has only kanji/kana, the Latin part is in
`mplus_j10r-iso-W5.bdf`, and half-width kana is in
`mplus_j10r-jisx0201.bdf`. These are fragments of the same design, and
listing them separately would show up as several incomplete fonts
(PixelMplus's "complete" file has 0/94 printable ASCII characters — not
even a space).

Attribution rule: file B is a subset of A if and only if B's stem equals
A's stem plus a `-` or `_` and a suffix. When multiple candidates exist,
take the longest A.
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
    """Returns {main file: [subset file, ...]}; a main file with no subsets maps to an empty list."""
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
        # A parent file might itself be someone else's subset — walk up to the root.
        while parent in parents:
            parent = parents[parent]
        out.setdefault(parent, []).append(child)
    for v in out.values():
        v.sort()
    return out


def merge(base: ParsedFont,
          extras: list[ParsedFont]) -> tuple[ParsedFont, list[str], list[ParsedFont]]:
    """Fill in codepoints from extras that base doesn't have.

    Returns (merged result, notes, fonts that couldn't be merged). Fonts
    that fail to merge must be kept by the caller as separate variants,
    otherwise those glyphs would just vanish.

    Mergeability is judged purely by pixel size: BDF glyphs carry their
    own baseline-relative offsets, so differing typeface-level
    ascent/descent doesn't block merging — take the max across all
    sources so every glyph fits.
    """
    notes: list[str] = []
    have = {g.cp for g in base.glyphs}
    added: list = []
    rejected: list[ParsedFont] = []
    for e in extras:
        if e.pixel_size != base.pixel_size:
            notes.append(
                f"{e.file_name}: pixel size differs from the base file ({e.pixel_size}px vs "
                f"{base.pixel_size}px), not merged, kept as its own variant"
            )
            rejected.append(e)
            continue
        new = [g for g in e.glyphs if g.cp not in have]
        have.update(g.cp for g in new)
        added.extend(new)
        base.ascent = max(base.ascent, e.ascent)
        base.descent = max(base.descent, e.descent)
        notes.append(f"{e.file_name}: merged {len(new)} glyphs")
    if not added:
        return base, notes, rejected

    base.glyphs = sorted(base.glyphs + added, key=lambda g: g.cp)
    xoff = min(g.bbx for g in base.glyphs)
    yoff = min(g.bby for g in base.glyphs)
    bw = max(g.bbx + g.bbw for g in base.glyphs) - xoff
    bh = max(g.bby + g.bbh for g in base.glyphs) - yoff
    base.bbox = (bw, bh, xoff, yoff)
    return base, notes, rejected
