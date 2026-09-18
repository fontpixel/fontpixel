"""Upgrade cached downloadable BDFs without rebuilding vector font downloads."""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from opf.downloads import _entry, _gz, _source_bdf_bytes
from opf.parsers.bdf import parse_bdf


def upgrade_cached_bdfs(entry: dict, detail: dict, downloads: list[dict],
                        data: Path, out: Path) -> list[dict]:
    if entry.get("bdfPreviewVersion") == 1:
        return downloads
    replacements: dict[str, bytes] = {}
    updated = []
    for item in downloads:
        if item["kind"] != "bdf":
            updated.append(item)
            continue
        vid = item["variantId"]
        font = parse_bdf(out / item["file"], entry["slug"])
        # Older cached exports retained source encodings, including a few
        # merged BDFs labelled with their source registry. Their existing
        # rendering data is the authority during this one-time migration.
        folder = data / "packs" / entry["slug"] / vid
        manifest_path = folder / "manifest.json"
        if manifest_path.exists():
            from opf.glyphpack import read_chunk  # legacy cache migration only

            manifest = json.loads(manifest_path.read_text())
            font.glyphs = sorted(
                (g for r in manifest["ranges"] for g in read_chunk(folder / r["file"])),
                key=lambda g: g.cp,
            )
        metrics = detail["metrics"][vid]
        font.pixel_size = metrics["pixelSize"]
        font.ascent, font.descent = metrics["ascent"], metrics["descent"]
        font.bbox = tuple(metrics["bbox"])
        variant = next(v for v in entry["variants"] if v["id"] == vid)
        if len(font.glyphs) != variant["glyphs"]:
            raise ValueError(f"{entry['slug']}/{vid}: cached BDF glyph count mismatch")
        raw = _source_bdf_bytes(font)
        replacements[f"{vid}.bdf"] = raw
        updated.append(_entry(entry["slug"], vid, "bdf", item["file"], _gz(raw), out))
    for i, item in enumerate(updated):
        if item["kind"] != "zip":
            continue
        buf = io.BytesIO()
        with zipfile.ZipFile(out / item["file"]) as src, \
                zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as dest:
            for info in src.infolist():
                dest.writestr(info, replacements.get(info.filename, src.read(info.filename)))
        updated[i] = _entry(entry["slug"], None, "zip", item["file"], buf.getvalue(), out)
    entry["bdfPreviewVersion"] = 1
    return updated
