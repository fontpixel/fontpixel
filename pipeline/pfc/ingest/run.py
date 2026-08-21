"""导入执行器:manifest.toml → fonts/<slug>/,幂等,产出导入报告。

用法:python -m pfc.ingest.run --manifest ingest/manifest.toml \
        --src ../pixel-font-collection-fonts --dest fonts [--only slug] \
        [--report docs/import-report.md]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import tempfile
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from pfc.ingest.bdfwrite import write_bdf
from pfc.ingest.extract import extract_zip
from pfc.ingest.kbitx import convert_kbitx
from pfc.ingest.otb import convert_otb

TODAY = "2026-08-21"

_TOML_TEMPLATE = """\
name = "{name}"
name_zh = "{name_zh}"
author = "{author}"
homepage = "{homepage}"
repository = "{repository}"
description = ""
form = "{form}"  # UNVERIFIED:导入时预填,待人工复核
vibes = {vibes}  # UNVERIFIED
converted_from = "{converted_from}"
provenance = "{provenance}"
added = "{added}"
"""


@dataclass
class IngestReport:
    imported: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    files_written: int = 0
    files_unchanged: int = 0
    errors: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _place(src_bytes: bytes, target: Path, report: IngestReport) -> bool:
    """写入文件,内容相同则跳过;返回是否有变化。"""
    if target.exists() and hashlib.sha256(src_bytes).hexdigest() == _sha(target):
        report.files_unchanged += 1
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(src_bytes)
    report.files_written += 1
    return True


def _ingest_family(fam: dict, src_root: Path, dest_root: Path,
                   report: IngestReport) -> bool:
    slug = fam["slug"]
    source = src_root / fam["source"]
    dest = dest_root / slug
    changed = False

    if fam.get("zip"):
        with tempfile.TemporaryDirectory() as td:
            files = extract_zip(source / fam["zip"], fam.get("zip_take", ["*.bdf"]),
                                Path(td))
            for f in sorted(files):
                changed |= _place(f.read_bytes(), dest / f.name, report)

    for pat in fam.get("take", []):
        matched = [
            p for p in sorted(source.rglob("*"))
            if p.is_file() and fnmatch.fnmatch(p.name, pat)
        ]
        if not matched:
            report.errors.append(f"{slug}: take 无匹配 {pat}")
        for p in matched:
            changed |= _place(p.read_bytes(), dest / p.name, report)

    convert = fam.get("convert", "")
    for pat in fam.get("convert_take", []):
        matched = [
            p for p in sorted(source.rglob("*"))
            if p.is_file() and fnmatch.fnmatch(p.name, pat)
        ]
        if not matched:
            report.errors.append(f"{slug}: convert_take 无匹配 {pat}")
        for p in matched:
            if convert == "otb":
                for suffix, pf in convert_otb(p, slug):
                    with tempfile.TemporaryDirectory() as td:
                        tmp = Path(td) / "x.bdf"
                        write_bdf(pf, tmp)
                        changed |= _place(
                            tmp.read_bytes(), dest / f"{p.stem}-{suffix}.bdf", report
                        )
            elif convert == "kbitx":
                pf = convert_kbitx(p, slug)
                with tempfile.TemporaryDirectory() as td:
                    tmp = Path(td) / "x.bdf"
                    write_bdf(pf, tmp)
                    changed |= _place(tmp.read_bytes(), dest / f"{p.stem}.bdf", report)
            else:
                report.errors.append(f"{slug}: 未知 convert 模式 {convert}")

    for lf in fam.get("license_files", []):
        matched = [
            p for p in sorted(source.rglob("*"))
            if p.is_file() and fnmatch.fnmatch(p.name, lf)
        ]
        if matched:
            changed |= _place(matched[0].read_bytes(), dest / matched[0].name, report)
        else:
            report.errors.append(f"{slug}: 许可证文件未找到 {lf}")

    toml_path = dest / "family.toml"
    if not toml_path.exists():
        provenance = fam.get("provenance_url", "")
        prov = f"导入自 {fam['source']}"
        if provenance:
            prov += f";上游 {provenance}"
        if convert:
            prov += f";由 {convert} 转换"
        toml_path.write_text(
            _TOML_TEMPLATE.format(
                name=fam.get("name", slug),
                name_zh=fam.get("name_zh", ""),
                author=fam.get("author", ""),
                homepage=fam.get("homepage", ""),
                repository=fam.get("repository", ""),
                form=fam.get("form", ""),
                vibes=str(fam.get("vibes", [])).replace("'", '"'),
                converted_from=convert if convert in ("ttf", "otf", "woff2") else "",
                provenance=prov,
                added=TODAY,
            ),
            encoding="utf-8",
        )
        changed = True
    return changed


def run_manifest(manifest_path: Path, src_root: Path, dest_root: Path,
                 only: str | None = None, report_path: Path | None = None
                 ) -> IngestReport:
    data = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    report = IngestReport()
    for fam in data.get("family", []):
        slug = fam["slug"]
        if only and slug != only:
            continue
        try:
            changed = _ingest_family(fam, src_root, dest_root, report)
        except Exception as e:  # noqa: BLE001 - 单家族失败不阻塞批量导入
            report.errors.append(f"{slug}: {e}")
            continue
        (report.imported if changed else report.skipped).append(slug)
    for todo in data.get("todo", []):
        report.notes.append(f"待议:{todo.get('source', '?')} — {todo.get('reason', '')}")
    if report_path:
        _write_report(report, report_path, data)
    return report


def _write_report(report: IngestReport, path: Path, data: dict) -> None:
    lines = [
        "# 导入报告",
        "",
        f"生成时间:{TODAY}(由 pfc.ingest.run 生成,重跑覆盖)",
        "",
        f"- manifest 家族数:{len(data.get('family', []))}",
        f"- 本次有变化:{len(report.imported)};无变化跳过:{len(report.skipped)}",
        f"- 文件写入:{report.files_written};未变:{report.files_unchanged}",
        "",
    ]
    if report.imported:
        lines += ["## 本次导入/更新", ""]
        lines += [f"- {s}" for s in report.imported]
        lines.append("")
    if report.errors:
        lines += ["## 错误", ""]
        lines += [f"- {e}" for e in report.errors]
        lines.append("")
    if report.notes:
        lines += ["## 待人工决定", ""]
        lines += [f"- {n}" for n in report.notes]
        lines.append("")
    lines += [
        "## 风格标注待复核",
        "",
        "family.toml 中带 `# UNVERIFIED` 注释的 form/vibes 为导入时预填,",
        "请逐一复核后删除该注释。",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--src", type=Path, required=True)
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--only", default=None)
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()
    report = run_manifest(args.manifest, args.src, args.dest, args.only, args.report)
    print(f"imported={len(report.imported)} skipped={len(report.skipped)} "
          f"files={report.files_written} unchanged={report.files_unchanged}")
    for e in report.errors:
        print(f"  error: {e}")


if __name__ == "__main__":
    main()
