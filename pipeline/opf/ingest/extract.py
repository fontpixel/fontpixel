"""压缩包中按 glob 抽取文件（zip 与 tar 系）。

上游发布形态不统一：GitHub 的 Release 资产多是 zip，而 X11 时代的字体包
（ohsnap／termsyn／jmk-x11-fonts 等）几乎都是 .tar.gz，许可证原文往往只存在于
包内（仓库目录树里只有编译好的 pcf）。两种格式都要能按 basename glob 取文件。
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
    """按 basename glob 抽取,返回落盘路径列表。zip 与 tar 系通用。

    同名文件以包内首次出现者为准（tar 的增量成员不会覆盖先落盘的同名文件）。
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
    """向后兼容的别名；新代码用 extract_archive。"""
    return extract_archive(zip_path, take, dest)
