"""UW ttyp0's official release → Unicode BDF.

Upstream distributes "fontspecific" master BDFs (`CHARSET_REGISTRY "UW"`,
ENCODING is the font's internal ordinal, glyph names look like `LtCapALdot`)
and generates the encoded fonts at install time with its own Makefile:
`bin/bdfmangle` applies `VARIANTS.dat` and `mgl/unicode.mgl` (PUT mappings
plus conditional IFDEF/IFUNDEF … COPYTO fallbacks), and each odd size
(11/13/15/17) is the next even size run through `bin/mkshallow` with the
odd-size supplement laid over it -- the odd-size master files alone hold only
~240 glyphs.

This module runs that build unchanged (`./configure`, then
`make bdf GEN_BDF=1`; needs sh, GNU make and perl) in a scratch copy of the
release and rewrites each `genbdf/t0-<size>-uni.bdf` as a canonical BDF named
after its master file. An earlier version re-implemented only the PUT lines
of `unicode.mgl`, which silently dropped every COPYTO glyph (74 in v1.3,
among them U+002A) and cannot evaluate the IFDEF conditions added in v2.0.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from opf.ingest.bdfwrite import write_bdf
from opf.parsers.bdf import parse_bdf


def _run(cmd: list[str], cwd: Path) -> None:
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode != 0:
        tail = r.stdout.decode("utf-8", "replace")[-500:]
        raise RuntimeError(f"{' '.join(cmd)} failed: {tail}")


def build_upstream(repo: Path, work: Path) -> list[Path]:
    """Run upstream's Unicode BDF build in a copy of `repo` under `work`; returns genbdf/*-uni.bdf."""
    if not (repo / "mgl" / "unicode.mgl").exists():
        raise FileNotFoundError(f"missing {repo / 'mgl' / 'unicode.mgl'}")
    tree = work / repo.name
    shutil.copytree(repo, tree, symlinks=True)
    _run(["sh", "./configure"], tree)
    # GEN_BDF is off in upstream's TARGETS.dat; sizes come from TARGETS_BDF.dat.
    _run(["make", "bdf", "GEN_BDF=1", "ENCODINGS_BDF=uni"], tree)
    out = sorted((tree / "genbdf").glob("t0-*-uni.bdf"))
    if not out:
        raise RuntimeError(f"{repo}: the upstream build produced no genbdf/t0-*-uni.bdf")
    return out


def build_all(repo: Path, dest: Path) -> list[tuple[str, int]]:
    """Build the release into dest (replacing its t0-*.bdf); returns [(filename, glyph count), ...]."""
    dest.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, int]] = []
    with tempfile.TemporaryDirectory() as tmp:
        built = build_upstream(repo, Path(tmp))
        # A size dropped upstream must not linger from the previous import.
        for stale in dest.glob("t0-*.bdf"):
            stale.unlink()
        for src in built:
            name = src.name.removesuffix("-uni.bdf") + ".bdf"
            font = parse_bdf(src, dest.name)
            font.file_name = name
            write_bdf(font, dest / name)
            out.append((name, len(font.glyphs)))
    return out


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="UW ttyp0 → Unicode BDF")
    ap.add_argument("--repo", type=Path, required=True, help="unpacked uw-ttyp0-x.y directory")
    ap.add_argument("--dest", type=Path, required=True, help="the fonts/uw-ttyp0 directory")
    args = ap.parse_args()
    for name, n in build_all(args.repo, args.dest):
        print(f"{name}: {n} glyphs")


if __name__ == "__main__":
    main()
