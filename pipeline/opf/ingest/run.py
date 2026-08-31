"""导入执行器：manifest.toml → fonts/<slug>/，幂等，产出导入报告。

用法：python -m opf.ingest.run --manifest ingest/manifest.toml \
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

from opf.ingest.bdfwrite import write_bdf
from opf.ingest.extract import extract_archive, is_tar
from opf.ingest.kbitx import convert_kbitx
from opf.ingest.otb import convert_otb

TODAY = "2026-08-31"

def _q(v: str) -> str:
    """TOML 基本字符串转义。清单里的说明文字含引号很常见。

    控制字符必须一并转义:TOML 规范禁止基本字符串里出现裸控制字符,漏掉
    \r、\b、\f 之类会生成解析不了的 family.toml。
    """
    out = []
    for ch in str(v):
        esc = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r",
               "\t": "\\t", "\b": "\\b", "\f": "\\f"}.get(ch)
        if esc is not None:
            out.append(esc)
        elif ch < " " or ch == "\x7f":
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return "".join(out)


def _arr(items) -> str:
    return "[" + ", ".join(f'"{_q(i)}"' for i in items) + "]"


def _render_toml(fam: dict, provenance: str, provenance_en: str,
                 converted_from: str, added: str) -> str:
    """按现有 family.toml 的字段顺序渲染：中文块 → 英文块 → [license]。

    清单没给的字段一律留空/省略，交人工补；form/vibes 打 UNVERIFIED 标记。
    """
    authors = fam.get("authors") or [a for a in [fam.get("author", "")] if a]
    lines = [
        f'name = "{_q(fam.get("name", fam["slug"]))}"',
    ]
    if fam.get("name_zh"):
        lines.append(f'name_zh = "{_q(fam["name_zh"])}"')
    lines += [
        f"authors = {_arr(authors)}",
        f'homepage = "{_q(fam.get("homepage", ""))}"',
        f'repository = "{_q(fam.get("repository", ""))}"',
        f'description = "{_q(fam.get("description", ""))}"',
    ]
    mark = "" if fam.get("form_verified") else "  # UNVERIFIED：导入时预填，待人工复核"
    lines.append(f'form = "{_q(fam.get("form", ""))}"{mark}')
    lines.append(
        f"vibes = {_arr(fam.get('vibes', []))}"
        + ("" if fam.get("form_verified") else "  # UNVERIFIED")
    )
    if fam.get("aliases"):
        lines.append(f"aliases = {_arr(fam['aliases'])}")
    if fam.get("merge_subsets"):
        lines.append("merge_subsets = true")
    lines += [
        f'converted_from = "{_q(converted_from)}"',
        f'provenance = "{_q(provenance)}"',
        f'added = "{_q(added)}"',
        "",
        f'name_en = "{_q(fam.get("name_en") or fam.get("name", fam["slug"]))}"',
        f"authors_en = {_arr(fam.get('authors_en') or authors)}",
    ]
    if fam.get("description_en"):
        lines.append(f'description_en = "{_q(fam["description_en"])}"')
    lines.append(f'provenance_en = "{_q(provenance_en)}"')

    lic = fam.get("license")
    if lic:
        lines += ["", "[license]"]
        lines.append(f'spdx = "{_q(lic.get("spdx", ""))}"')
        lines.append(f'name = "{_q(lic.get("name", ""))}"')
        lines.append(f'confidence = "{_q(lic.get("confidence", "manual"))}"')
        if lic.get("file"):
            lines.append(f'file = "{_q(lic["file"])}"')
        lines.append(f'note = "{_q(lic.get("note", ""))}"')
        if lic.get("name_en"):
            lines.append(f'name_en = "{_q(lic["name_en"])}"')
        if lic.get("note_en"):
            lines.append(f'note_en = "{_q(lic["note_en"])}"')

    merge = fam.get("merge")
    if merge:
        lines += ["", "[merge]"]
        for k, v in merge.items():
            lines.append(f'"{_q(k)}" = {_arr(v)}')

    # 逐变体覆写（上游元数据有错时用，例如 PIXEL_SIZE 被复制粘贴写错）。
    for fname, ov in (fam.get("variants") or {}).items():
        lines += ["", f'[variants."{_q(fname)}"]']
        for k, v in ov.items():
            if isinstance(v, bool):
                lines.append(f"{k} = {str(v).lower()}")
            elif isinstance(v, int):
                lines.append(f"{k} = {v}")
            else:
                lines.append(f'{k} = "{_q(v)}"')

    return "\n".join(lines) + "\n"


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
    """写入文件，内容相同则跳过；返回是否有变化。"""
    if target.exists() and hashlib.sha256(src_bytes).hexdigest() == _sha(target):
        report.files_unchanged += 1
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(src_bytes)
    report.files_written += 1
    return True


class _DestGuard:
    """同一家族内，凡是会写到同一个目标文件名的来源都要报出来。

    原先逐个模式各查各的，跨模式的冲突（take = ["a/x.bdf", "b/x.bdf"]）与
    license_files 的冲突都漏掉了；而 take 是后者覆盖前者、license_files 是
    只取第一个，静默地由排序决定收录哪一份。
    """

    def __init__(self, slug: str, report: IngestReport) -> None:
        self.slug = slug
        self.report = report
        self.seen: dict[str, Path] = {}

    def add(self, matched: list[Path], pat: str, prefix: str = "") -> None:
        for p in matched:
            name = prefix + p.name
            first = self.seen.get(name)
            if first is not None and first != p:
                self.report.errors.append(
                    f"{self.slug}: 目标文件名 {name} 有多个来源（{first} 与 {p}，"
                    f"模式 {pat}）；请改用带 “/” 的路径模式指明其一"
                )
            else:
                self.seen[name] = p


def _matches(path: Path, source: Path, pat: str) -> bool:
    """含 “/” 的模式（或以 “./” 开头的）按相对 source 的路径匹配，否则按文件名匹配。

    源目录根部的同名文件用 “./LICENSE” 这样的写法锚定。

    路径模式逐段匹配：fnmatch 的 “*” 会跨过 “/”，直接拿整条路径去匹配会让
    “fonts/*.ttf” 命中 “fonts/nested/x.ttf”，把本想排除的子目录又收进来。
    """
    if pat.startswith("./"):
        pat = pat[2:]
    elif "/" not in pat:
        return fnmatch.fnmatch(path.name, pat)
    try:
        rel = path.relative_to(source).as_posix()
    except ValueError:
        return False
    segs, pats = rel.split("/"), pat.split("/")
    if len(segs) != len(pats):
        return False
    return all(fnmatch.fnmatch(a, b) for a, b in zip(segs, pats))


def _collect(source: Path, pat: str) -> list[Path]:
    return [p for p in sorted(source.rglob("*")) if p.is_file() and _matches(p, source, pat)]


def _ingest_family(fam: dict, src_root: Path, dest_root: Path,
                   report: IngestReport) -> bool:
    slug = fam["slug"]
    source = src_root / fam["source"]
    dest = dest_root / slug
    changed = False
    guard = _DestGuard(slug, report)

    zip_list = ([fam["zip"]] if fam.get("zip") else []) + list(fam.get("zips", []))
    for zp in zip_list:
        with tempfile.TemporaryDirectory() as td:
            files = extract_archive(source / zp, fam.get("zip_take", ["*.bdf"]),
                                    Path(td))
            if not files:
                report.errors.append(f"{slug}: zip {zp} 无匹配文件")
            for f in sorted(files):
                changed |= _place(f.read_bytes(), dest / f.name, report)

    for pat in fam.get("take", []):
        matched = _collect(source, pat)
        if not matched:
            report.errors.append(f"{slug}: take 无匹配 {pat}")
        guard.add(matched, pat)
        for p in matched:
            changed |= _place(p.read_bytes(), dest / p.name, report)

    # take_from:{前缀 = [模式...]}。上游把同一设计按解析度分成两套目录、
    # 文件名却完全相同（Adobe 的 75dpi 与 100dpi 都叫 helvR12.bdf，实为
    # 12px 与 17px），直接按原名落地会互相覆盖，得加前缀区分。
    for prefix, pats in (fam.get("take_from") or {}).items():
        for pat in pats:
            matched = _collect(source, pat)
            if not matched:
                report.errors.append(f"{slug}: take_from 无匹配 {pat}")
            guard.add(matched, pat, prefix)
            for p in matched:
                changed |= _place(p.read_bytes(), dest / f"{prefix}{p.name}", report)

    convert = fam.get("convert", "")
    for pat in fam.get("convert_take", []):
        matched = _collect(source, pat)
        if not matched:
            report.errors.append(f"{slug}: convert_take 无匹配 {pat}")
        guard.add(matched, pat)
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
            elif convert == "ttf":
                from opf.ingest.rasterize import detect_native_ppem, rasterize_ttf

                # ppem 可给整数（整族一档），也可给 {文件名 = 档位} 的表——
                # 同一设计的多个尺寸在一个家族里时（KH ドット的道玄坂 12／16），
                # 单一 ppem 不够用。上游若自带内嵌点阵，按其标称档位取到的就是
                # 内嵌位图本身，比栅格化轮廓更准。
                cfg = fam.get("ppem")
                ppem = cfg.get(p.name) if isinstance(cfg, dict) else cfg
                if not ppem:
                    ppem = detect_native_ppem(p)
                if ppem is None:
                    report.errors.append(
                        f"{slug}: {p.name} 原生格点判定失败,不自动转制(可在清单中手填 ppem)"
                    )
                    continue
                pf = rasterize_ttf(p, int(ppem), slug)
                with tempfile.TemporaryDirectory() as td:
                    tmp = Path(td) / "x.bdf"
                    write_bdf(pf, tmp)
                    changed |= _place(
                        tmp.read_bytes(), dest / f"{p.stem}-{ppem}px.bdf", report
                    )
            else:
                report.errors.append(f"{slug}: 未知 convert 模式 {convert}")

    for lf in fam.get("license_files", []):
        matched = _collect(source, lf)
        guard.add(matched, lf)
        if matched:
            changed |= _place(matched[0].read_bytes(), dest / matched[0].name, report)
        else:
            report.errors.append(f"{slug}: 许可证文件未找到 {lf}")

    # 许可证只存在于压缩包内的上游（X11 时代的 .tar.gz 字体包尤其常见）。
    lic_from = fam.get("license_from", "")
    if lic_from:
        # 先按 source 相对路径找，找不到再按 --src 根目录找（许可证包常与字体
        # 目录平级，例如 <repo>/archives/<x>.tar.gz 对 <repo>/bitmap/<x>/）。
        arc = source / lic_from
        if not arc.exists():
            arc = src_root / lic_from
        if arc.is_file() and not (is_tar(arc) or arc.suffix.lower() == ".zip"):
            # 上游把许可证放在别的仓库/目录里（如字体只有编译产物、许可证在源码库）。
            changed |= _place(arc.read_bytes(), dest / arc.name, report)
            arc = None
    if lic_from and arc is not None:
        with tempfile.TemporaryDirectory() as td:
            files = extract_archive(arc,
                                    fam.get("license_take", ["LICENSE*", "COPYING*"]),
                                    Path(td))
            if not files:
                report.errors.append(f"{slug}: license_from {lic_from} 无匹配文件")
            for f in sorted(files):
                changed |= _place(f.read_bytes(), dest / f.name, report)

    dest.mkdir(parents=True, exist_ok=True)
    toml_path = dest / "family.toml"
    if not toml_path.exists():
        upstream = fam.get("provenance_url", "")
        prov = f"导入自 {fam['source']}"
        prov_en = f"Imported from {fam['source']}"
        if upstream:
            prov += f"；上游 {upstream}"
            prov_en += f"; upstream {upstream}"
        if convert:
            prov += f"；由 {convert} 转换"
            prov_en += f"; converted from {convert}"
        toml_path.write_text(
            _render_toml(fam, prov, prov_en,
                         convert if convert in ("ttf", "otf", "woff2") else "",
                         TODAY),
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
        report.notes.append(f"待议：{todo.get('source', '?')} — {todo.get('reason', '')}")
    if report_path:
        _write_report(report, report_path, data)
    return report


def _write_report(report: IngestReport, path: Path, data: dict) -> None:
    lines = [
        "# 导入报告",
        "",
        f"生成时间：{TODAY}（由 opf.ingest.run 生成，重跑覆盖）",
        "",
        f"- manifest 家族数：{len(data.get('family', []))}",
        f"- 本次有变化：{len(report.imported)}；无变化跳过：{len(report.skipped)}",
        f"- 文件写入：{report.files_written}；未变：{report.files_unchanged}",
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
        "family.toml 中带 `# UNVERIFIED` 注释的 form/vibes 为导入时预填，",
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
