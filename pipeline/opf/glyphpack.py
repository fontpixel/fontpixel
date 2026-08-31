"""Glyph pack v1 writer (contract C1/C2).

Chunking: codepoints are grouped into 256-aligned blocks; a chunk breaks
when the gap to the next used block exceeds 16 blocks, or the estimated
raw size exceeds 48KB. gzip mtime=0 keeps output deterministic.
"""

from __future__ import annotations

import gzip
import json
import struct
from pathlib import Path

from opf.familymeta import VariantDesc
from opf.model import Glyph, ParsedFont, row_bytes
from opf.samples import CORE_TEXT

_MAGIC = b"PFG1"
_VERSION = 1
_ENTRY = struct.Struct("<IhBBbbI")
_HEADER = struct.Struct("<4sBBHII")
_RAW_LIMIT = 32 * 1024  # roughly ≤16KB after gzip (measured bitmap entropy gives a ~0.45 compression ratio)
_BLOCK_GAP = 16


def _glyph_bitmap_size(g: Glyph) -> int:
    return g.bbh * row_bytes(g.bbw)


def plan_chunks(glyphs: list[Glyph]) -> list[tuple[int, int]]:
    """Return a list of 256-aligned (start, end) half-open intervals."""
    if not glyphs:
        return []
    # Estimated size of each used block
    block_size: dict[int, int] = {}
    for g in glyphs:
        b = g.cp >> 8
        block_size[b] = block_size.get(b, 0) + _ENTRY.size + _glyph_bitmap_size(g)
    blocks = sorted(block_size)
    ranges: list[tuple[int, int]] = []
    start = blocks[0]
    prev = blocks[0]
    acc = block_size[blocks[0]]
    for b in blocks[1:]:
        if b - prev > _BLOCK_GAP or acc + block_size[b] > _RAW_LIMIT:
            ranges.append((start << 8, (prev + 1) << 8))
            start = b
            acc = 0
        acc += block_size[b]
        prev = b
    ranges.append((start << 8, (prev + 1) << 8))
    return ranges


def _encode_chunk(glyphs: list[Glyph], start: int, end: int,
                  warnings: list[str]) -> bytes:
    usable: list[Glyph] = []
    for g in glyphs:
        if g.bbw > 255 or g.bbh > 255 or not (-128 <= g.bbx <= 127) or not (
            -128 <= g.bby <= 127
        ) or not (-32768 <= g.dwidth <= 32767):
            warnings.append(f"glyph U+{g.cp:04X} metrics out of pack range, skipped")
            continue
        usable.append(g)
    head = _HEADER.pack(_MAGIC, _VERSION, 0, len(usable), start, end)
    index = bytearray()
    bitmaps = bytearray()
    for g in usable:
        index += _ENTRY.pack(g.cp, g.dwidth, g.bbw, g.bbh, g.bbx, g.bby, len(bitmaps))
        bitmaps += g.rows
    return head + bytes(index) + bytes(bitmaps)


def _gz(data: bytes) -> bytes:
    return gzip.compress(data, compresslevel=9, mtime=0)


def write_packs(f: ParsedFont, v: VariantDesc, meta_name: str, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    warnings: list[str] = []
    by_cp = {g.cp: g for g in f.glyphs}

    ranges_meta = []
    for start, end in plan_chunks(f.glyphs):
        chunk_glyphs = [g for g in f.glyphs if start <= g.cp < end]
        raw = _encode_chunk(chunk_glyphs, start, end, warnings)
        gz = _gz(raw)
        name = f"{start:08x}-{end:08x}.bin.gz"
        (out_dir / name).write_bytes(gz)
        ranges_meta.append({
            "start": start, "end": end, "file": name,
            "gzBytes": len(gz), "glyphs": len(chunk_glyphs),
        })

    core_set = {ord(c) for c in CORE_TEXT + meta_name}
    core_glyphs = [by_cp[cp] for cp in sorted(core_set) if cp in by_cp]
    core_raw = _encode_chunk(core_glyphs, 0, 0x110000, warnings)
    core_gz = _gz(core_raw)
    (out_dir / "core.bin.gz").write_bytes(core_gz)

    f.warnings.extend(warnings)
    manifest = {
        "version": 1,
        "slug": f.family_slug,
        "variantId": v.id,
        "pixelSize": f.pixel_size,
        "ascent": f.ascent,
        "descent": f.descent,
        "glyphCount": len(f.glyphs),
        "core": {"file": "core.bin.gz", "gzBytes": len(core_gz),
                 "glyphs": len(core_glyphs)},
        "ranges": ranges_meta,
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"),
                   sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def read_chunk(path: Path) -> list[Glyph]:
    raw = gzip.decompress(path.read_bytes())
    magic, version, _flags, count, _start, _end = _HEADER.unpack_from(raw, 0)
    if magic != _MAGIC or version != _VERSION:
        raise ValueError(f"{path}: bad chunk header")
    glyphs: list[Glyph] = []
    bitmap_base = _HEADER.size + count * _ENTRY.size
    for i in range(count):
        cp, dwidth, bbw, bbh, bbx, bby, off = _ENTRY.unpack_from(
            raw, _HEADER.size + i * _ENTRY.size
        )
        size = bbh * row_bytes(bbw)
        rows = raw[bitmap_base + off : bitmap_base + off + size]
        glyphs.append(Glyph(cp=cp, name=f"cp{cp:04X}", dwidth=dwidth, bbw=bbw,
                            bbh=bbh, bbx=bbx, bby=bby, rows=rows))
    return glyphs
