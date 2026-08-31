"""Extract files from an archive by glob (zip and the tar family).

Upstream release formats aren't consistent: GitHub Release assets are mostly
zip, while X11-era font packages (ohsnap, termsyn, jmk-x11-fonts, etc.) are
almost all .tar.gz, and the license text often only exists inside the archive
(the repo tree itself has only the compiled pcf). Both formats need to support
extracting files by basename glob.
"""

from __future__ import annotations

import fnmatch
import tarfile
import zipfile
from pathlib import Path

_TAR_SUFFIXES = (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2", ".tar.xz", ".txz")


def is_tar(path: Path) -> bool:
    name = path.name.lower()
    return any(name.endswith(s) for s in _TAR_SUFFIXES)


def extract_archive(archive_path: Path, take: list[str], dest: Path) -> list[Path]:
    """Extract by basename glob, returning the list of written paths. Works for both zip and the tar family.

    For same-named files, the first occurrence in the archive wins (a later
    tar member won't overwrite a same-named file already written to disk).
    """
    dest.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    seen: set[str] = set()

    def want(member_name: str) -> str | None:
        base = Path(member_name).name
        if base in seen or not any(fnmatch.fnmatch(base, pat) for pat in take):
            return None
        return base

    if is_tar(archive_path):
        with tarfile.open(archive_path) as t:
            for info in t.getmembers():
                if not info.isfile():
                    continue
                base = want(info.name)
                if base is None:
                    continue
                fh = t.extractfile(info)
                if fh is None:
                    continue
                (dest / base).write_bytes(fh.read())
                seen.add(base)
                out.append(dest / base)
    else:
        with zipfile.ZipFile(archive_path) as z:
            for info in z.infolist():
                if info.is_dir():
                    continue
                base = want(info.filename)
                if base is None:
                    continue
                (dest / base).write_bytes(z.read(info))
                seen.add(base)
                out.append(dest / base)
    return out


def extract_zip(zip_path: Path, take: list[str], dest: Path) -> list[Path]:
    """Backward-compatible alias; new code should use extract_archive."""
    return extract_archive(zip_path, take, dest)
