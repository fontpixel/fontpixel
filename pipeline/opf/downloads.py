"""Download artifact build: bdf.gz / pcf.gz per variant, a zip per family (with license and provenance README).

All output is byte-for-byte deterministic: gzip mtime=0, zip entry
timestamps pinned to 1980-01-01.
"""

from __future__ import annotations

import gzip
import hashlib
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from opf.familymeta import VariantDesc
from opf.ingest.bdfwrite import write_bdf
from opf.model import ParsedFont
from opf.ttfexport import build_ttf, name_records

ROUND_MAX_GLYPHS = 20000  # above this glyph count, only produce the square vector variant
_ZIP_DATE = (1980, 1, 1, 0, 0, 0)


def _names_match(font, family: str, style: str, copyright_: str) -> bool:
    values = name_records(family, style, copyright_)
    keys = {0: "copyright", 1: "familyName", 2: "styleName", 3: "uniqueFontIdentifier",
            4: "fullName", 5: "version", 6: "psName"}
    return all(font["name"].getDebugName(id) == values[key] for id, key in keys.items())


def _restyle_ttf(raw: bytes, family: str, style: str, copyright_: str) -> bytes:
    """Rewrite only the name table of an existing TTF, leaving glyf untouched — avoids re-vectorizing.

    recalcTimestamp=False is required: the default save() sets
    head.modified to the current time, which would break byte-level
    determinism. A test asserts that the bytes produced this way are
    identical to a full rebuild with the new metadata.
    """
    import io

    from fontTools.fontBuilder import FontBuilder
    from fontTools.ttLib import TTFont

    from opf.ttfexport import FIXED_TIMESTAMP

    f = TTFont(io.BytesIO(raw), recalcTimestamp=False, lazy=True)
    if _names_match(f, family, style, copyright_):
        return raw
    FontBuilder(font=f).setupNameTable(name_records(family, style, copyright_))
    f["head"].created = f["head"].modified = FIXED_TIMESTAMP
    buf = io.BytesIO()
    f.save(buf)
    return buf.getvalue()


def _restyle_woff2(raw: bytes, family: str, copyright_: str) -> bytes:
    """The woff2 counterpart of _restyle_ttf: swap the name table, recompress."""
    import io
    import tempfile

    from fontTools.fontBuilder import FontBuilder
    from fontTools.ttLib import TTFont

    from opf.ttfexport import FIXED_TIMESTAMP

    f = TTFont(io.BytesIO(raw), recalcTimestamp=False)
    style = f["name"].getDebugName(2) or "Regular"
    if _names_match(f, family, style, copyright_):
        return raw
    FontBuilder(font=f).setupNameTable(name_records(family, style, copyright_))
    f["head"].created = f["head"].modified = FIXED_TIMESTAMP
    with tempfile.TemporaryDirectory() as td:
        ttf = Path(td) / "f.ttf"
        f.flavor = None
        f.save(str(ttf))
        return _woff2(ttf) or raw


def _rezip_readme(raw: bytes, readme_text: str) -> bytes:
    """Replace only the README inside the zip, carrying every other member over as-is (timestamps still pinned)."""
    import io

    src = io.BytesIO(raw)
    buf = io.BytesIO()
    with zipfile.ZipFile(src) as check:
        if check.read("README.txt") == readme_text.encode("utf-8"):
            return raw
    src.seek(0)
    with zipfile.ZipFile(src) as zin, \
            zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = (readme_text.encode("utf-8") if item.filename == "README.txt"
                    else zin.read(item.filename))
            info = zipfile.ZipInfo(item.filename, date_time=_ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zout.writestr(info, data)
    return buf.getvalue()


def refresh_downloads_metadata(
    entries: list[dict],
    out: Path,
    readme_text: str,
    family_display: str,
    copyright_line: str,
) -> list[dict]:
    """Refresh new metadata into existing downloads: swap the TTF name table, swap the zip's README.

    Glyph outlines and BDF/PCF are unrelated to metadata and are left
    as-is — this whole path exists precisely to avoid re-vectorizing
    (half an hour for 131 families). Returns the updated entries (size
    and sha256 change); BDF/PCF entries are returned unchanged.
    """
    fresh: list[dict] = []
    for e in entries:
        kind, path = e["kind"], out / e["file"]
        if not path.exists():           # output was pruned; let it fall back to a full rebuild
            return []
        raw = path.read_bytes()
        if kind.startswith("ttf"):
            data = _restyle_ttf(raw, family_display, _ttf_style(raw), copyright_line)
        elif kind.startswith("woff2"):
            # Same name-table swap, then recompress; a woff2 carries the same
            # name records as the TTF it came from, so leaving it alone here
            # would publish the old family name and copyright.
            data = _restyle_woff2(raw, family_display, copyright_line)
        elif kind == "zip":
            data = _rezip_readme(raw, readme_text)
        else:
            fresh.append(e)
            continue
        fresh.append(_entry(e["family"], e["variantId"], kind, e["file"], data, out))
    return fresh


def _ttf_style(raw: bytes) -> str:
    """Read back the TTF's own styleName (name ID 2).

    style is determined by variant grouping (weight/spacing/script
    subset), which is structural information that doesn't change on a
    cache hit, so reading it back from the output is enough — no need to
    reparse the font.
    """
    import io

    from fontTools.ttLib import TTFont

    rec = TTFont(io.BytesIO(raw), lazy=True)["name"].getDebugName(2)
    return rec or "Regular"


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


# Above this size, compress for speed rather than for the last few percent.
_WOFF2_FAST_BYTES = 1_500_000


def _woff2(ttf_path: Path) -> bytes | None:
    """Recompress a TTF as woff2, or None when brotli isn't available.

    fontTools' defaults are far too slow here. It applies the woff2 glyf
    transform in pure Python — 13s on a 7MB CJK font, for about 12% off the
    result — and hands brotli its top quality, another 12s. Skipping the
    transform and using quality 9 on big fonts turns 25s into 0.5s for 41%
    more bytes, which is the right trade when the whole collection is rebuilt
    on every font change. Small fonts keep quality 11: it costs milliseconds
    there. The output is a plain woff2 either way; table transforms are
    optional in the format and every browser reads both.
    """
    import tempfile

    from fontTools.ttLib import TTFont
    try:
        import fontTools.ttLib.woff2 as woff2mod
        from fontTools.ttLib.woff2 import WOFF2FlavorData
    except ImportError:
        return None

    size = ttf_path.stat().st_size
    quality = 9 if size > _WOFF2_FAST_BYTES else 11
    orig = woff2mod.brotli.compress
    woff2mod.brotli.compress = (
        lambda data, **kw: orig(data, **{**kw, "quality": quality})
    )
    try:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "f.woff2"
            font = TTFont(str(ttf_path), recalcTimestamp=False)
            font.flavor = "woff2"
            font.flavorData = WOFF2FlavorData(transformedTables=set())
            font.save(str(out))
            return out.read_bytes()
    except Exception:  # noqa: BLE001 - a missing woff2 must not fail the download set
        return None
    finally:
        woff2mod.brotli.compress = orig


def _source_bdf_bytes(f: ParsedFont) -> bytes:
    """One canonical Unicode BDF, shared by downloads and browser rendering.

    Preserve every parsed bitmap, metric and unencoded alternate. The source
    files remain untouched; only the downloadable representation is normalized.
    """
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "x.bdf"
        write_bdf(f, tmp)
        return tmp.read_bytes()


def _pcf_bytes(f: ParsedFont, bdf_data: bytes) -> bytes | None:
    name = f.path.name.lower()
    # A merged font must be regenerated from the merged BDF, not copied
    if not f.merged and name.endswith(".pcf"):
        return f.path.read_bytes()
    if not f.merged and name.endswith(".pcf.gz"):
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
    family_display: str = "",
    copyright_line: str = "",
) -> list[dict]:
    out.mkdir(parents=True, exist_ok=True)
    family_display = family_display or slug
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
            f.warnings.append(f"{v.id}: PCF generation failed, BDF only")

    from opf.vectorize import build_vector_ttf

    # Bitmap TTF: all sizes of the same font (same weight/spacing/script
    # subset) get packed into one file.
    groups: dict[tuple[str, str, str], list[tuple[ParsedFont, VariantDesc]]] = {}
    for f, v in fonts:
        groups.setdefault((v.weight, v.spacing, v.script_subset or ""), []).append((f, v))
    multi = len(groups) > 1
    # Only put dimensions that actually vary between groups into the
    # filename, to avoid redundancy like sq-monospaced-bold.ttf.
    varying = [
        i for i in range(3)
        if len({key[i] for key in groups}) > 1
    ]
    for key, items in sorted(groups.items()):
        weight, spacing, script = key
        parts = [key[i] for i in varying if key[i]]
        suffix = "-".join([slug] + parts) if parts else slug
        style = " ".join(p.capitalize() for p in parts) if parts else weight.capitalize()
        name = f"{suffix}.ttf"
        import tempfile as _tf

        from opf.ttfexport import MAX_GLYPHS

        union = len({g.cp for f, _ in items for g in f.glyphs})
        # Upstream sometimes splits an oversized font into multiple pieces
        # (combined they'd exceed the TTF glyph count limit) — export per piece in that case.
        batches = ([(name, [it for it in items])] if union + 1 <= MAX_GLYPHS
                   else [(f"{suffix}-{v.id}.ttf", [(f, v)]) for f, v in items])
        for fname, batch in batches:
            try:
                with _tf.TemporaryDirectory() as td:
                    tmp = Path(td) / "f.ttf"
                    build_ttf([f for f, _ in batch], family_display,
                              style or "Regular", tmp, copyright_=copyright_line)
                    entries.append(_entry(slug, None, "ttf", fname,
                                          tmp.read_bytes(), out))
            except Exception as e:  # noqa: BLE001 - a TTF failure doesn't affect BDF/PCF downloads
                for f, _ in batch:
                    f.warnings.append(f"TTF export failed ({fname}): {e}")

        # Vector TTF: only export the largest pixel size for each typeface.
        # Vector outlines already scale arbitrarily, so exporting every
        # size of the same typeface would just multiply the download size.
        rf, rv = max(items, key=lambda it: (it[1].size, it[1].id))
        # Round dots trace each pixel as its own ring and can't merge runs
        # the way squares can, so an oversized font can reach tens of MB in
        # a single file — hence glyph counts above the threshold get only the square variant.
        shapes = ["square"] if len(rf.glyphs) > ROUND_MAX_GLYPHS else ["square", "round"]
        for shape in shapes:
            vname = f"{suffix}-{rv.size}px-{shape}.ttf"
            try:
                with _tf.TemporaryDirectory() as td:
                    tmp = Path(td) / "v.ttf"
                    build_vector_ttf(rf, family_display, style or "Regular", tmp,
                                     shape=shape, copyright_=copyright_line)
                    entries.append(_entry(slug, None, f"ttf-{shape}", vname,
                                          tmp.read_bytes(), out))
                    # Web use wants woff2, and only the vector outlines are
                    # safe to serve that way: a browser's handling of the
                    # bitmap TTF's embedded strikes is inconsistent, whereas
                    # these outlines render anywhere and stay pixel-crisp at
                    # integer multiples of the design size.
                    w2 = _woff2(tmp)
                    if w2 is not None:
                        entries.append(_entry(
                            slug, None, f"woff2-{shape}",
                            f"{suffix}-{rv.size}px-{shape}.woff2", w2, out))
            except Exception as e:  # noqa: BLE001 - a single file failing doesn't affect other downloads
                rf.warnings.append(f"vector TTF export failed ({vname}): {e}")

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
