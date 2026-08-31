"""Write a canonical BDF from a ParsedFont (used for format conversion and generating BDF downloads from PCF sources)."""

from __future__ import annotations

from pathlib import Path

from opf.model import ParsedFont, row_bytes


def _prop_line(key: str, value: str | int) -> str:
    if isinstance(value, int):
        return f"{key} {value}"
    return f'{key} "{value.replace(chr(34), chr(34) * 2)}"'


def write_bdf(f: ParsedFont, out: Path) -> None:
    lines: list[str] = ["STARTFONT 2.1"]
    font_name = str(f.props.get("FONT", "")) or (
        f"-opf-{f.family_slug}-medium-r-normal--{f.pixel_size}-"
        f"{f.pixel_size * 10}-75-75-p-{f.pixel_size * 10}-iso10646-1"
    )
    lines.append(f"FONT {font_name}")
    lines.append(f"SIZE {f.pixel_size} 75 75")
    lines.append(f"FONTBOUNDINGBOX {f.bbox[0]} {f.bbox[1]} {f.bbox[2]} {f.bbox[3]}")

    props: dict[str, str | int] = dict(f.props)
    props.pop("FONT", None)
    props["FONT_ASCENT"] = f.ascent
    props["FONT_DESCENT"] = f.descent
    props.setdefault("PIXEL_SIZE", f.pixel_size)
    lines.append(f"STARTPROPERTIES {len(props)}")
    for k in props:
        lines.append(_prop_line(k, props[k]))
    lines.append("ENDPROPERTIES")

    lines.append(f"CHARS {len(f.glyphs)}")
    for g in f.glyphs:
        lines.append(f"STARTCHAR {g.name or f'uni{g.cp:04X}'}")
        lines.append(f"ENCODING {g.cp}")
        swidth = round(g.dwidth * 1000 / max(1, f.pixel_size))
        lines.append(f"SWIDTH {swidth} 0")
        lines.append(f"DWIDTH {g.dwidth} 0")
        lines.append(f"BBX {g.bbw} {g.bbh} {g.bbx} {g.bby}")
        lines.append("BITMAP")
        nb = row_bytes(g.bbw)
        for y in range(g.bbh):
            lines.append(g.rows[y * nb : (y + 1) * nb].hex().upper())
        lines.append("ENDCHAR")
    lines.append("ENDFONT")
    out.write_text("\n".join(lines) + "\n", encoding="latin-1", errors="replace")
