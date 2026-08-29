"""zip 中按 glob 抽取字体文件。"""

from __future__ import annotations

import fnmatch
import zipfile
from pathlib import Path


def extract_zip(zip_path: Path, take: list[str], dest: Path) -> list[Path]:
    """按 basename glob 抽取,返回落盘路径列表。"""
    dest.mkdir(parents=True, exist_ok=True)
    out: list[Path] = []
    with zipfile.ZipFile(zip_path) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            base = Path(info.filename).name
            if not any(fnmatch.fnmatch(base, pat) for pat in take):
                continue
            target = dest / base
            target.write_bytes(z.read(info))
            out.append(target)
    return out
