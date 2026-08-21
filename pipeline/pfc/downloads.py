"""下载物构建:每变体 bdf.gz / pcf.gz,每家族 zip(含许可证与来源 README)。

全部产物字节级确定:gzip mtime=0、zip 条目时间戳固定 1980-01-01。
"""

from __future__ import annotations

import gzip
import hashlib
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from pfc.familymeta import VariantDesc
from pfc.ingest.bdfwrite import write_bdf
from pfc.model import ParsedFont

_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def _gz(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9, mtime=0)


def _entry(slug: str, variant_id: str | None, kind: str, file: str, data: bytes,
           out: Path) -> dict:
    (out / file).write_bytes(data)
    return {
        "family": slug,
        "variantId": variant_id,
        "kind": kind,
        "file": file,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _source_bdf_bytes(f: ParsedFont) -> bytes:
    """变体的 BDF 原文;源是 .gz 先解压,源是 PCF 则由 ParsedFont 反写。"""
    name = f.path.name.lower()
    if name.endswith(".bdf"):
        return f.path.read_bytes()
    if name.endswith(".bdf.gz"):
        return gzip.decompress(f.path.read_bytes())
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "x.bdf"
        write_bdf(f, tmp)
        return tmp.read_bytes()


def _pcf_bytes(f: ParsedFont, bdf_data: bytes) -> bytes | None:
    name = f.path.name.lower()
    if name.endswith(".pcf"):
        return f.path.read_bytes()
    if name.endswith(".pcf.gz"):
        return gzip.decompress(f.path.read_bytes())
    if shutil.which("bdftopcf") is None:
        return None
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "x.bdf"
        dst = Path(td) / "x.pcf"
        src.write_bytes(bdf_data)
        r = subprocess.run(["bdftopcf", str(src), "-o", str(dst)],
                           capture_output=True)
        if r.returncode != 0 or not dst.exists():
            return None
        return dst.read_bytes()


def build_downloads(
    slug: str,
    family_dir: Path,
    fonts: list[tuple[ParsedFont, VariantDesc]],
    license_files: list[str],
    readme_text: str,
    out: Path,
) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    entries: list[dict] = []
    zip_members: list[tuple[str, bytes]] = []

    for f, v in fonts:
        bdf_data = _source_bdf_bytes(f)
        entries.append(_entry(slug, v.id, "bdf", f"{slug}--{v.id}.bdf.gz",
                              _gz(bdf_data), out))
        zip_members.append((f"{v.id}.bdf", bdf_data))
        pcf_data = _pcf_bytes(f, bdf_data)
        if pcf_data is not None:
            entries.append(_entry(slug, v.id, "pcf", f"{slug}--{v.id}.pcf.gz",
                                  _gz(pcf_data), out))
        else:
            f.warnings.append(f"{v.id}: PCF 生成失败,仅提供 BDF")

    for lf in license_files:
        p = family_dir / lf
        if p.exists():
            zip_members.append((lf, p.read_bytes()))
    zip_members.append(("README.txt", readme_text.encode("utf-8")))

    import io

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in zip_members:
            info = zipfile.ZipInfo(name, date_time=_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    entries.append(_entry(slug, None, "zip", f"{slug}.zip", buf.getvalue(), out))
    return entries
