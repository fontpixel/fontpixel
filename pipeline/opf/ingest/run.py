"""Import executor: manifest.toml -> fonts/<slug>/, idempotent, produces an import report.

Usage: python -m opf.ingest.run --manifest ingest/manifest.toml \
        --src ../pixel-font-collection-fonts --dest fonts [--only slug] \
        [--report docs/import-report.md]
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import re
import tempfile
import tomllib
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from opf.ingest.bdfwrite import write_bdf
from opf.ingest.extract import extract_archive, is_tar
from opf.ingest.kbitx import convert_kbitx
from opf.ingest.otb import convert_otb
from opf.familymeta import normalize_forms

# Seeds `added` in newly generated family.toml files. Hardcoded on purpose:
# a rerun must not churn the inclusion dates of families already on file.
TODAY = "2026-09-03"

# Everything from this marker onward in an import report is hand-maintained and
# survives a rerun; only the generated head above it is replaced. Matching is on
# the prefix alone, so rewording the sentence -- or translating it, as happened
# on 2026-09-03 -- cannot strand an existing report.
MANUAL_MARKER_PREFIX = "<!-- opf:manual"
MANUAL_MARKER = (
    MANUAL_MARKER_PREFIX
    + " — the hand-maintained inclusion record below is never touched by opf.ingest.run -->"
)


def _q(v: str) -> str:
    """TOML basic-string escaping. Description text in the manifest commonly contains quotes.

    Control characters must be escaped too: the TOML spec forbids bare control
    characters in basic strings, and missing one (\r, \b, \f, etc.) produces
    a family.toml that fails to parse.
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
    """Render in the same field order as existing family.toml files: Chinese block -> English block -> [license].

    Fields the manifest doesn't provide are left blank/omitted for manual
    follow-up; forms/vibes are marked UNVERIFIED.
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
    forms = normalize_forms(fam.get("forms", fam.get("form", [])))
    lines.append(f'forms = {_arr(forms)}{mark}')
    lines.append(
        f"vibes = {_arr(fam.get('vibes', []))}"
        + ("" if fam.get("form_verified") else "  # UNVERIFIED")
    )
    if fam.get("aliases"):
        lines.append(f"aliases = {_arr(fam['aliases'])}")
    if fam.get("default_variant"):
        lines.append(f'default_variant = "{_q(fam["default_variant"])}"')
    if fam.get("source_kind"):
        lines.append(f'source_kind = "{_q(fam["source_kind"])}"')
    if fam.get("source_formats"):
        lines.append(f"source_formats = {_arr(fam['source_formats'])}")
    if fam.get("export_name"):
        lines.append(f'export_name = "{_q(fam["export_name"])}"')
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

    # Per-variant overrides (for when upstream metadata is wrong, e.g. PIXEL_SIZE copy-pasted incorrectly).
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
    """Write the file, skipping if content is unchanged; returns whether anything changed."""
    if target.exists() and hashlib.sha256(src_bytes).hexdigest() == _sha(target):
        report.files_unchanged += 1
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(src_bytes)
    report.files_written += 1
    return True


class _DestGuard:
    """Within one family, flag any sources that would write to the same destination filename.

    Previously each pattern was checked in isolation, so cross-pattern
    conflicts (take = ["a/x.bdf", "b/x.bdf"]) and license_files conflicts both
    slipped through; take lets the later source overwrite the earlier one,
    while license_files just takes the first match — silently letting sort
    order decide which copy gets included.
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
                    f"{self.slug}: destination filename {name} has more than one source "
                    f"({first} and {p}, pattern {pat}); use a path pattern with a "
                    f"\u201c/\u201d to name the one you want"
                )
            else:
                self.seen[name] = p


def _matches(path: Path, source: Path, pat: str) -> bool:
    """A pattern containing "/" (or starting with "./") matches against the path relative to source; otherwise it matches by filename.

    A same-named file at the source root is anchored with a pattern like "./LICENSE".

    Path patterns are matched segment by segment: fnmatch's "*" crosses "/",
    so matching the whole path directly would let "fonts/*.ttf" match
    "fonts/nested/x.ttf", pulling in a subdirectory meant to be excluded.
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
                report.errors.append(f"{slug}: zip {zp} matched no files")
            for f in sorted(files):
                changed |= _place(f.read_bytes(), dest / f.name, report)

    for pat in fam.get("take", []):
        matched = _collect(source, pat)
        if not matched:
            report.errors.append(f"{slug}: take matched nothing for {pat}")
        guard.add(matched, pat)
        for p in matched:
            changed |= _place(p.read_bytes(), dest / p.name, report)

    # take_from: {prefix = [pattern...]}. Upstream splits the same design into
    # two directories by resolution, with identical filenames (Adobe's 75dpi
    # and 100dpi both use helvR12.bdf, which are really 12px and 17px);
    # writing them under the original name would overwrite each other, so a
    # prefix is added to distinguish them.
    for prefix, pats in (fam.get("take_from") or {}).items():
        for pat in pats:
            matched = _collect(source, pat)
            if not matched:
                report.errors.append(f"{slug}: take_from matched nothing for {pat}")
            guard.add(matched, pat, prefix)
            for p in matched:
                changed |= _place(p.read_bytes(), dest / f"{prefix}{p.name}", report)

    convert = fam.get("convert", "")
    for pat in fam.get("convert_take", []):
        matched = _collect(source, pat)
        if not matched:
            report.errors.append(f"{slug}: convert_take matched nothing for {pat}")
        guard.add(matched, pat)
        for p in matched:
            if convert == "otb":
                for suffix, pf in convert_otb(p, slug, all_glyphs=bool(fam.get("all_glyphs", False))):
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
            elif convert in ("t-mat-8x8", "font8x8"):
                from opf.ingest.header8x8 import convert_font8x8, convert_tmat

                pf = (convert_tmat if convert == "t-mat-8x8" else convert_font8x8)(p, slug)
                report.notes.extend(f"{slug}: {warning}" for warning in pf.warnings)
                with tempfile.TemporaryDirectory() as td:
                    tmp = Path(td) / "x.bdf"
                    write_bdf(pf, tmp)
                    changed |= _place(tmp.read_bytes(), dest / pf.file_name, report)
            elif convert == "spritesheet":
                from opf.ingest.spritesheet import convert_spritesheet

                specs = fam["sprite_maps"][p.name]
                for spec in specs if isinstance(specs, list) else [specs]:
                    pf = convert_spritesheet(p, slug, spec)
                    with tempfile.TemporaryDirectory() as td:
                        tmp = Path(td) / "x.bdf"
                        write_bdf(pf, tmp)
                        changed |= _place(tmp.read_bytes(), dest / pf.file_name, report)
            elif convert == "ttf":
                from opf.ingest.rasterize import detect_native_ppem, rasterize_ttf

                # ppem can be a single integer (one size for the whole
                # family), or a {filename = size} table -- a single ppem
                # isn't enough when a family bundles multiple sizes of the
                # same design (e.g. KH Dot's Dogenzaka 12/16). If upstream
                # ships an embedded bitmap, taking it at its nominal size
                # gets the embedded bitmap itself, which is more accurate
                # than rasterizing the outline.
                cfg = fam.get("ppem")
                ppem = cfg.get(p.name) if isinstance(cfg, dict) else cfg
                if not ppem:
                    ppem = detect_native_ppem(p)
                if ppem is None:
                    report.errors.append(
                        f"{slug}: {p.name} native grid could not be determined; not converted "
                        f"automatically (fill in ppem by hand in the manifest)"
                    )
                    continue
                instances = fam.get("instances") or [{}]
                if isinstance(instances, dict):
                    if p.name not in instances:
                        raise ValueError(f"{slug}: no instances configured for {p.name}")
                    instances = instances[p.name]
                for instance in instances:
                    stem = instance.get("name", p.stem)
                    if instance and not re.fullmatch(r"[A-Za-z0-9_-]+", stem):
                        raise ValueError(f"{slug}: invalid instance name: {stem}")
                    grid = fam.get("grid_units")
                    if isinstance(grid, dict):
                        grid = grid.get(p.name)
                    pf = rasterize_ttf(
                        p, int(ppem), slug,
                        hinting=bool(fam.get("hinting", False)),
                        all_glyphs=bool(fam.get("all_glyphs", False)),
                        axes=instance.get("axes"),
                        glyph_offsets=instance.get("glyph_offsets", fam.get("glyph_offsets")),
                        pixel_offset=instance.get("pixel_offset", fam.get("pixel_offset")),
                        grid_units=grid,
                    )
                    pf.props["FONT"] = f"{stem}-{ppem}px"
                    if fam.get("export_name"):
                        pf.props["FONT"] = f'{fam["export_name"].replace(" ", "-")}-{ppem}px'
                        pf.props["FAMILY_NAME"] = fam["export_name"]
                    if instance.get("weight"):
                        pf.props["WEIGHT_NAME"] = instance["weight"]
                    report.notes.extend(f"{slug}: {warning}" for warning in pf.warnings)
                    with tempfile.TemporaryDirectory() as td:
                        tmp = Path(td) / "x.bdf"
                        write_bdf(pf, tmp)
                        changed |= _place(
                            tmp.read_bytes(), dest / f"{stem}-{ppem}px.bdf", report
                        )
            else:
                report.errors.append(f"{slug}: unknown convert mode {convert}")

    for lf in fam.get("license_files", []):
        matched = _collect(source, lf)
        guard.add(matched, lf)
        if matched:
            changed |= _place(matched[0].read_bytes(), dest / matched[0].name, report)
        else:
            report.errors.append(f"{slug}: licence file not found: {lf}")

    # Upstreams where the license only exists inside an archive (especially common for X11-era .tar.gz font packages).
    lic_from = fam.get("license_from", "")
    if lic_from:
        # First look relative to source, then fall back to the --src root
        # (the license archive is often a sibling of the font directory,
        # e.g. <repo>/archives/<x>.tar.gz alongside <repo>/bitmap/<x>/).
        arc = source / lic_from
        if not arc.exists():
            arc = src_root / lic_from
        if arc.is_file() and not (is_tar(arc) or arc.suffix.lower() == ".zip"):
            # Upstream keeps the license in a separate repo/directory (e.g. the font is compiled-output-only, with the license in the source repo).
            changed |= _place(arc.read_bytes(), dest / arc.name, report)
            arc = None
    if lic_from and arc is not None:
        with tempfile.TemporaryDirectory() as td:
            files = extract_archive(arc,
                                    fam.get("license_take", ["LICENSE*", "COPYING*"]),
                                    Path(td))
            if not files:
                report.errors.append(f"{slug}: license_from {lic_from} matched no files")
            for f in sorted(files):
                changed |= _place(f.read_bytes(), dest / f.name, report)

    dest.mkdir(parents=True, exist_ok=True)
    toml_path = dest / "family.toml"
    if not toml_path.exists():
        # Cite the upstream the font actually came from, not the path it happens
        # to occupy in the local collection: provenance is shown to readers on
        # the font page, and the collection's directory layout means nothing to
        # them. The source path stays recorded in the manifest, which is what a
        # rerun reads. Only when no upstream URL is known does the path stand in.
        upstream = fam.get("provenance_url", "")
        origin = upstream or fam["source"]
        prov = f"导入自 {origin}"
        prov_en = f"Imported from {origin}"
        if convert:
            prov += f"；由 {convert} 转换"
            prov_en += f"; converted from {convert}"
        toml_path.write_text(
            _render_toml(fam, prov, prov_en,
                         convert if convert in ("ttf", "otf", "woff2") else "",
                         fam.get("added", TODAY)),
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
        except Exception as e:  # noqa: BLE001 - a single family's failure shouldn't block the batch import
            report.errors.append(f"{slug}: {e}")
            continue
        (report.imported if changed else report.skipped).append(slug)
    for todo in data.get("todo", []):
        # reason_en where the manifest carries one, the Chinese reason otherwise --
        # same fallback the description/note fields use.
        why = todo.get("reason_en") or todo.get("reason", "")
        report.notes.append(f"Pending: {todo.get('source', '?')} — {why}")
    if report_path:
        _write_report(report, report_path, data)
    return report


def _write_report(report: IngestReport, path: Path, data: dict) -> None:
    lines = [
        "# Import Report",
        "",
        f"Generated: {date.today().isoformat()} "
        "(generated by opf.ingest.run; overwritten on rerun)",
        "",
        f"- Families in manifest: {len(data.get('family', []))}",
        f"- Changed this run: {len(report.imported)}; "
        f"skipped unchanged: {len(report.skipped)}",
        f"- Files written: {report.files_written}; "
        f"unchanged: {report.files_unchanged}",
        "",
    ]
    if report.imported:
        lines += ["## Imported/Updated This Run", ""]
        lines += [f"- {s}" for s in report.imported]
        lines.append("")
    if report.errors:
        lines += ["## Errors", ""]
        lines += [f"- {e}" for e in report.errors]
        lines.append("")
    if report.notes:
        lines += ["## Pending Manual Decision", ""]
        lines += [f"- {n}" for n in report.notes]
        lines.append("")
    lines += [
        "## Style Annotations Pending Review",
        "",
        "The form/vibes fields in family.toml carrying a `# UNVERIFIED` comment "
        "were pre-filled at import time;",
        "please review each one and remove the comment afterward.",
        "",
    ]
    generated = "\n".join(lines)

    # Everything from MANUAL_MARKER onward is hand-written history -- the
    # per-batch inclusion reasoning, licence determinations and removal
    # records the README points at. Only the generated head above it is ours
    # to replace.
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        at = existing.find(MANUAL_MARKER_PREFIX)
        if at < 0:
            raise ValueError(
                f"{path} exists but carries no manual-record marker; refusing to "
                f"overwrite, since the file may hold hand-written content. To allow "
                f"it, put a line reading \u201c{MANUAL_MARKER}\u201d above the "
                f"hand-written section, or point --report somewhere else."
            )
        generated += "\n" + existing[at:]
    else:
        generated += "\n" + MANUAL_MARKER + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(generated, encoding="utf-8")


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
