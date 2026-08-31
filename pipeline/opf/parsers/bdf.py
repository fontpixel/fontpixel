"""BDF 解析器。

容忍常见方言:CRLF、位图行长度不符(截断/补零并记警告)、重复
ENCODING(保留首个)、缺失 ascent/descent(从 FONTBOUNDINGBOX 推导)。
"""

from __future__ import annotations

import gzip
import re
from pathlib import Path

from opf.model import Glyph, ParsedFont, row_bytes
from opf.parsers.charset_map import decode_cp, is_unicode_registry

_INT_RE = re.compile(r"^-?\d+$")


def _read_lines(path: Path) -> list[str]:
    opener = gzip.open if path.name.endswith(".gz") else open
    with opener(path, "rt", encoding="latin-1") as fh:  # type: ignore[operator]
        return [ln.rstrip("\r\n") for ln in fh]


def _prop_value(raw: str) -> str | int:
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        return raw[1:-1].replace('""', '"')
    if _INT_RE.match(raw):
        return int(raw)
    return raw


def _normalize_row(hexline: str, nbytes: int, warnings: list[str], glyph: str) -> bytes:
    hexline = hexline.strip()
    if len(hexline) % 2 == 1:
        warnings.append(f"glyph {glyph}: odd-length bitmap hex line padded")
        hexline += "0"
    try:
        raw = bytes.fromhex(hexline)
    except ValueError:
        warnings.append(f"glyph {glyph}: invalid bitmap hex line replaced with zeros")
        raw = b""
    if len(raw) != nbytes:
        if len(raw) > nbytes:
            warnings.append(f"glyph {glyph}: bitmap row too long, truncated")
            raw = raw[:nbytes]
        else:
            warnings.append(f"glyph {glyph}: bitmap row too short, zero-padded")
            raw = raw.ljust(nbytes, b"\x00")
    return raw


def parse_bdf(path: Path, family_slug: str, *,
              remap_charset: bool = True) -> ParsedFont:
    """remap_charset=False 时保留原始 ENCODING（供按字形名自行重映射的场景）。"""
    lines = _read_lines(path)
    warnings: list[str] = []
    props: dict[str, str | int] = {}
    glyphs: dict[int, Glyph] = {}
    bbox = (0, 0, 0, 0)
    size_line: tuple[int, int, int] | None = None
    xlfd_pixel_size = 0
    xlfd_setwidth = ""
    declared_chars: int | None = None
    missing_dwidth = 0

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        i += 1
        if not line:
            continue
        key, _, rest = line.partition(" ")
        if key == "FONT":
            # XLFD 名的第 7 段就是 PIXEL_SIZE，比 SIZE 行可靠：不少工具
            # （如 Bits'n'Picas）把 SIZE 的点数字段直接写成像素数，按
            # 点数×dpi/72 换算会算出 17px、22px 这种不存在的尺寸。
            xf = rest.split("-")
            if len(xf) >= 15:
                if xf[7].isdigit():
                    xlfd_pixel_size = int(xf[7])
                # 第 5 段是 SETWIDTH（Normal / Condensed / Expanded 等）；
                # 不少工具不写 SETWIDTH_NAME 属性，只在字体名里带
                xlfd_setwidth = xf[5]
        elif key == "SIZE":
            parts = rest.split()
            if len(parts) >= 3:
                try:
                    size_line = (int(float(parts[0])), int(parts[1]), int(parts[2]))
                except ValueError:
                    warnings.append("unparsable SIZE line")
        elif key == "FONTBOUNDINGBOX":
            p = rest.split()
            if len(p) >= 4:
                bbox = (int(p[0]), int(p[1]), int(p[2]), int(p[3]))
        elif key == "STARTPROPERTIES":
            while i < n and not lines[i].startswith("ENDPROPERTIES"):
                pk, _, pv = lines[i].partition(" ")
                if pk:
                    props[pk] = _prop_value(pv)
                i += 1
            i += 1  # skip ENDPROPERTIES
        elif key == "CHARS":
            try:
                declared_chars = int(rest.strip())
            except ValueError:
                pass
        elif key == "STARTCHAR":
            name = rest.strip() or "?"
            enc = -1
            dwidth: int | None = None
            gb = (0, 0, 0, 0)
            rows = b""
            while i < n:
                cl = lines[i]
                i += 1
                ck, _, crest = cl.partition(" ")
                if ck == "ENCODING":
                    cparts = crest.split()
                    if cparts:
                        try:
                            enc = int(cparts[0])
                        except ValueError:
                            enc = -1
                elif ck == "DWIDTH":
                    cparts = crest.split()
                    if cparts:
                        try:
                            dwidth = int(cparts[0])
                        except ValueError:
                            pass
                elif ck == "BBX":
                    cparts = crest.split()
                    if len(cparts) >= 4:
                        gb = (int(cparts[0]), int(cparts[1]), int(cparts[2]), int(cparts[3]))
                elif ck == "BITMAP":
                    nbytes = row_bytes(gb[0])
                    out = bytearray()
                    got = 0
                    while i < n and lines[i].strip() != "ENDCHAR":
                        if got < gb[1]:
                            out += _normalize_row(lines[i], nbytes, warnings, name)
                        got += 1
                        i += 1
                    if got != gb[1]:
                        warnings.append(
                            f"glyph {name}: bitmap has {got} rows, BBX declares {gb[1]}"
                        )
                        while len(out) < gb[1] * nbytes:
                            out += b"\x00" * nbytes
                    rows = bytes(out)
                elif ck == "ENDCHAR":
                    break
                if cl.strip() == "ENDCHAR":
                    break
            if enc < 0:
                continue
            if enc in glyphs:
                warnings.append(f"duplicate ENCODING {enc}, keeping first")
                continue
            if not rows:
                rows = b"\x00" * (gb[1] * row_bytes(gb[0]))
            if dwidth is None:
                dwidth = -1  # 哨兵:解析完 pixel_size 后统一回退
                missing_dwidth += 1
            glyphs[enc] = Glyph(
                cp=enc, name=name, dwidth=dwidth,
                bbw=gb[0], bbh=gb[1], bbx=gb[2], bby=gb[3], rows=rows,
            )
        elif key == "ENDFONT":
            break

    if declared_chars is not None and declared_chars != len(glyphs) + 0:
        # 声明数含未编码字形属正常,只在少于实际时提示
        if declared_chars < len(glyphs):
            warnings.append(
                f"CHARS declares {declared_chars}, parsed {len(glyphs)} encoded glyphs"
            )

    if xlfd_setwidth and not props.get("SETWIDTH_NAME"):
        props["SETWIDTH_NAME"] = xlfd_setwidth

    pixel_size = 0
    ps = props.get("PIXEL_SIZE")
    if isinstance(ps, int) and ps > 0:
        pixel_size = ps
    elif xlfd_pixel_size > 0:
        pixel_size = xlfd_pixel_size
    elif size_line is not None:
        pixel_size = round(size_line[0] * size_line[2] / 72)
    if pixel_size <= 0:
        pixel_size = bbox[1]
        warnings.append("pixel size derived from FONTBOUNDINGBOX")

    asc = props.get("FONT_ASCENT")
    desc = props.get("FONT_DESCENT")
    if not isinstance(asc, int) or not isinstance(desc, int):
        asc = bbox[1] + bbox[3]
        desc = -bbox[3]
        warnings.append("ascent/descent derived from FONTBOUNDINGBOX")

    if missing_dwidth:
        # UnifontEX 等方言省略 DWIDTH:按单元格语义回退——
        # 墨迹超过半格视为全宽(= pixel_size),否则半宽。
        half = (pixel_size + 1) // 2
        for g in glyphs.values():
            if g.dwidth == -1:
                natural = g.bbw + max(g.bbx, 0)
                g.dwidth = pixel_size if natural > half else max(half, natural)
        warnings.append(
            f"{missing_dwidth} glyphs missing DWIDTH, cell-width fallback applied"
        )

    # 非 Unicode 字符集:按 CHARSET_REGISTRY 重映射码位。
    # 例外:有些字体(如 hurss DOS 系列)registry 写着 Johab,数据却已是
    # Unicode——用字形名(U+XXXX/uniXXXX)与 ENCODING 的吻合度识破。
    registry = str(props.get("CHARSET_REGISTRY", "")) if remap_charset else ""
    if registry and not is_unicode_registry(registry):
        name_re = re.compile(r"^(?:U\+?|uni)([0-9A-Fa-f]{4,6})$")
        sample = list(glyphs.values())[:200]
        named = [
            (g, m) for g in sample if (m := name_re.match(g.name)) is not None
        ]
        if len(named) >= 20 and all(
            int(m.group(1), 16) == g.cp for g, m in named
        ):
            warnings.append(
                f"charset {registry} ignored: glyph names confirm Unicode encoding"
            )
            registry = ""
    if registry and not is_unicode_registry(registry):
        cenc = str(props.get("CHARSET_ENCODING", "0"))
        warned: set[str] = set()
        remapped: dict[int, Glyph] = {}
        dropped = 0
        for g in glyphs.values():
            cp = decode_cp(g.cp, registry, cenc, warnings, warned)
            if cp is None or cp in remapped:
                dropped += 1
                continue
            g.cp = cp
            remapped[cp] = g
        if dropped:
            warnings.append(
                f"charset {registry}: {dropped} glyphs unmappable to Unicode, dropped"
            )
        glyphs = remapped

    file_name = path.name
    return ParsedFont(
        path=path,
        family_slug=family_slug,
        file_name=file_name,
        props=props,
        pixel_size=pixel_size,
        ascent=int(asc),
        descent=int(desc),
        bbox=bbox,
        glyphs=[glyphs[cp] for cp in sorted(glyphs)],
        warnings=warnings,
    )
