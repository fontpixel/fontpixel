"""PCF parser.

Reads the properties / metrics / bitmaps / encodings / glyph names /
accelerators tables; normalizes bit order, byte order, and row padding to the
BDF convention (rows are ceil(w/8) bytes, MSB-first bits, leftmost pixel in
the high bit); maps legacy charset code points to Unicode by CHARSET_REGISTRY.
"""

from __future__ import annotations

import gzip
import struct
from pathlib import Path

from opf.model import Glyph, ParsedFont, row_bytes
from opf.parsers.charset_map import decode_cp

PCF_PROPERTIES = 1 << 0
PCF_ACCELERATORS = 1 << 1
PCF_METRICS = 1 << 2
PCF_BITMAPS = 1 << 3
PCF_INK_METRICS = 1 << 4
PCF_BDF_ENCODINGS = 1 << 5
PCF_SWIDTHS = 1 << 6
PCF_GLYPH_NAMES = 1 << 7
PCF_BDF_ACCELERATORS = 1 << 8

PCF_COMPRESSED_METRICS = 0x100
PCF_BYTE_MASK = 1 << 2  # set = MSB byte order
PCF_BIT_MASK = 1 << 3  # set = MSB bit order

_BIT_REVERSE = bytes(int(f"{i:08b}"[::-1], 2) for i in range(256))


class _Reader:
    def __init__(self, data: bytes, pos: int, msb: bool):
        self.d = data
        self.p = pos
        self.e = ">" if msb else "<"

    def u8(self) -> int:
        v = self.d[self.p]
        self.p += 1
        return v

    def i16(self) -> int:
        (v,) = struct.unpack_from(self.e + "h", self.d, self.p)
        self.p += 2
        return v

    def u16(self) -> int:
        (v,) = struct.unpack_from(self.e + "H", self.d, self.p)
        self.p += 2
        return v

    def i32(self) -> int:
        (v,) = struct.unpack_from(self.e + "i", self.d, self.p)
        self.p += 4
        return v

    def skip(self, n: int) -> None:
        self.p += n


def _read_format(data: bytes, offset: int) -> tuple[int, _Reader]:
    (fmt,) = struct.unpack_from("<i", data, offset)
    return fmt, _Reader(data, offset + 4, bool(fmt & PCF_BYTE_MASK))


def _read_metric(r: _Reader, compressed: bool) -> tuple[int, int, int, int, int]:
    """Returns (lsb, rsb, width, ascent, descent)."""
    if compressed:
        lsb = r.u8() - 0x80
        rsb = r.u8() - 0x80
        w = r.u8() - 0x80
        asc = r.u8() - 0x80
        desc = r.u8() - 0x80
        return lsb, rsb, w, asc, desc
    lsb = r.i16()
    rsb = r.i16()
    w = r.i16()
    asc = r.i16()
    desc = r.i16()
    r.skip(2)  # attributes
    return lsb, rsb, w, asc, desc


def parse_pcf(path: Path, family_slug: str) -> ParsedFont:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rb") as fh:  # type: ignore[operator]
        data = fh.read()

    if data[:4] != b"\x01fcp":
        raise ValueError(f"{path}: not a PCF file")
    (count,) = struct.unpack_from("<i", data, 4)
    toc: dict[int, tuple[int, int, int]] = {}
    for i in range(count):
        typ, fmt, size, off = struct.unpack_from("<iiii", data, 8 + 16 * i)
        toc.setdefault(typ, (fmt, size, off))

    warnings: list[str] = []
    props: dict[str, str | int] = {}

    # --- properties ---
    if PCF_PROPERTIES in toc:
        fmt, r = _read_format(data, toc[PCF_PROPERTIES][2])
        nprops = r.i32()
        entries = [(r.i32(), r.u8(), r.i32()) for _ in range(nprops)]
        pad = (nprops * 9) % 4
        if pad:
            r.skip(4 - pad)
        strsize = r.i32()
        strings = data[r.p : r.p + strsize]

        def cstr(off: int) -> str:
            end = strings.find(b"\x00", off)
            return strings[off : end if end >= 0 else None].decode("latin-1")

        for name_off, is_str, value in entries:
            name = cstr(name_off)
            props[name] = cstr(value) if is_str else value

    # --- metrics ---
    if PCF_METRICS not in toc:
        raise ValueError(f"{path}: PCF has no metrics table")
    fmt, r = _read_format(data, toc[PCF_METRICS][2])
    compressed = bool(fmt & PCF_COMPRESSED_METRICS)
    n_glyphs = r.i16() if compressed else r.i32()
    metrics = [_read_metric(r, compressed) for _ in range(n_glyphs)]

    # --- bitmaps ---
    if PCF_BITMAPS not in toc:
        raise ValueError(f"{path}: PCF has no bitmaps table")
    fmt, r = _read_format(data, toc[PCF_BITMAPS][2])
    bm_count = r.i32()
    if bm_count != n_glyphs:
        warnings.append(f"bitmap count {bm_count} != metrics count {n_glyphs}")
    offsets = [r.i32() for _ in range(bm_count)]
    sizes = [r.i32() for _ in range(4)]
    bitmap_data = bytearray(data[r.p : r.p + sizes[fmt & 3]])

    bit_msb = bool(fmt & PCF_BIT_MASK)
    byte_msb = bool(fmt & PCF_BYTE_MASK)
    scan_unit = 1 << ((fmt >> 4) & 3)
    row_pad = 1 << (fmt & 3)
    if not bit_msb:
        bitmap_data = bytearray(bytes(bitmap_data).translate(_BIT_REVERSE))
    if byte_msb != bit_msb and scan_unit > 1:
        for i in range(0, len(bitmap_data) - scan_unit + 1, scan_unit):
            bitmap_data[i : i + scan_unit] = bitmap_data[i : i + scan_unit][::-1]

    def glyph_rows(idx: int, bbw: int, bbh: int) -> bytes:
        start = offsets[idx]
        stride = ((bbw + row_pad * 8 - 1) // (row_pad * 8)) * row_pad
        want = row_bytes(bbw)
        out = bytearray()
        for y in range(bbh):
            row = bitmap_data[start + y * stride : start + y * stride + want]
            out += bytes(row).ljust(want, b"\x00")
        return bytes(out)

    # --- glyph names ---
    names: list[str] = []
    if PCF_GLYPH_NAMES in toc:
        fmt, r = _read_format(data, toc[PCF_GLYPH_NAMES][2])
        cnt = r.i32()
        offs = [r.i32() for _ in range(cnt)]
        ssz = r.i32()
        sblob = data[r.p : r.p + ssz]
        for o in offs:
            end = sblob.find(b"\x00", o)
            names.append(sblob[o : end if end >= 0 else None].decode("latin-1"))

    # --- encodings ---
    if PCF_BDF_ENCODINGS not in toc:
        raise ValueError(f"{path}: PCF has no encoding table")
    fmt, r = _read_format(data, toc[PCF_BDF_ENCODINGS][2])
    min_c2 = r.i16()
    max_c2 = r.i16()
    min_b1 = r.i16()
    max_b1 = r.i16()
    r.skip(2)  # default char
    cols = max_c2 - min_c2 + 1
    registry = str(props.get("CHARSET_REGISTRY", "ISO10646"))
    cenc = str(props.get("CHARSET_ENCODING", "1"))

    glyphs: dict[int, Glyph] = {}
    warned: set[str] = set()
    total = (max_b1 - min_b1 + 1) * cols
    for i in range(total):
        gi = r.u16()
        if gi == 0xFFFF or gi >= n_glyphs:
            continue
        if min_b1 == 0 and max_b1 == 0:
            code = min_c2 + i
        else:
            code = ((min_b1 + i // cols) << 8) | (min_c2 + i % cols)
        cp = decode_cp(code, registry, cenc, warnings, warned)
        if cp is None or cp in glyphs:
            continue
        lsb, rsb, w, asc, desc = metrics[gi]
        bbw = max(0, rsb - lsb)
        bbh = max(0, asc + desc)
        glyphs[cp] = Glyph(
            cp=cp,
            name=names[gi] if gi < len(names) else f"cp{cp:04X}",
            dwidth=w,
            bbw=bbw,
            bbh=bbh,
            bbx=lsb,
            bby=-desc,
            rows=glyph_rows(gi, bbw, bbh),
        )

    # --- ascent/descent/pixel size ---
    asc_v = props.get("FONT_ASCENT")
    desc_v = props.get("FONT_DESCENT")
    for tbl in (PCF_BDF_ACCELERATORS, PCF_ACCELERATORS):
        if (not isinstance(asc_v, int)) and tbl in toc:
            fmt, r = _read_format(data, toc[tbl][2])
            r.skip(8)
            asc_v = r.i32()
            desc_v = r.i32()
    if not isinstance(asc_v, int) or not isinstance(desc_v, int):
        asc_v = max((g.bbh + g.bby for g in glyphs.values()), default=0)
        desc_v = max((-g.bby for g in glyphs.values()), default=0)
        warnings.append("ascent/descent derived from glyph metrics")

    ps = props.get("PIXEL_SIZE")
    pixel_size = ps if isinstance(ps, int) and ps > 0 else int(asc_v) + int(desc_v)

    if glyphs:
        xoff = min(g.bbx for g in glyphs.values())
        yoff = min(g.bby for g in glyphs.values())
        bw = max(g.bbx + g.bbw for g in glyphs.values()) - xoff
        bh = max(g.bby + g.bbh for g in glyphs.values()) - yoff
        bbox = (bw, bh, xoff, yoff)
    else:
        bbox = (0, 0, 0, 0)

    return ParsedFont(
        path=path,
        family_slug=family_slug,
        file_name=path.name,
        props=props,
        pixel_size=pixel_size,
        ascent=int(asc_v),
        descent=int(desc_v),
        bbox=bbox,
        glyphs=[glyphs[cp] for cp in sorted(glyphs)],
        warnings=warnings,
    )
