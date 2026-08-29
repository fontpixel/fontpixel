"""构建期预渲染:默认样例 SVG(SEO/无 JS)与 og:image PNG。

布局逻辑与 site/src/lib/render.ts 一致:LTR、无 shaping、\n 换行、
缺字画虚线占位框(advance = round(px/2)+1)。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fbf.model import Glyph, ParsedFont, row_bytes

LINE_GAP = 1


def _missing_advance(pixel_size: int) -> int:
    return round(pixel_size / 2) + 1


@dataclass
class _Placed:
    glyph: Glyph | None
    cp: int
    x: int
    line: int


def _layout(f: ParsedFont, text: str, max_width: int | None = None
            ) -> tuple[list[_Placed], int, int]:
    by_cp = {g.cp: g for g in f.glyphs}
    miss_adv = _missing_advance(f.pixel_size)
    placed: list[_Placed] = []
    line = x = 0
    max_w = 1
    for ch in text:
        if ch == "\n":
            line += 1
            x = 0
            continue
        cp = ord(ch)
        g = by_cp.get(cp)
        adv = max(g.dwidth, 0) if g else miss_adv
        if max_width and x > 0 and x + adv > max_width:
            line += 1
            x = 0
        placed.append(_Placed(glyph=g, cp=cp, x=x, line=line))
        x += adv
        max_w = max(max_w, x)
    lines = line + 1
    height = lines * (f.ascent + f.descent) + (lines - 1) * LINE_GAP
    return placed, max_w, height


def _glyph_runs(g: Glyph) -> list[tuple[int, int, int]]:
    """返回 (x, y, run_len) 列表,y 自位图顶部起。"""
    nb = row_bytes(g.bbw)
    runs: list[tuple[int, int, int]] = []
    for yy in range(g.bbh):
        base = yy * nb
        x = 0
        while x < g.bbw:
            byte = g.rows[base + (x >> 3)]
            if byte & (0x80 >> (x & 7)):
                start = x
                while x < g.bbw and g.rows[base + (x >> 3)] & (0x80 >> (x & 7)):
                    x += 1
                runs.append((start, yy, x - start))
            else:
                x += 1
    return runs


def sample_svg(f: ParsedFont, text: str, fg: str = "currentColor",
               max_width: int | None = None) -> str:
    placed, width, height = _layout(f, text, max_width)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'shape-rendering="crispEdges" role="img">'
    ]
    miss_adv = _missing_advance(f.pixel_size)
    for p in placed:
        baseline = p.line * (f.ascent + f.descent + LINE_GAP) + f.ascent
        if p.glyph is None:
            w = miss_adv - 1
            top = baseline - f.ascent + 1
            h = f.ascent - 2
            parts.append(
                f'<rect class="missing" x="{p.x}.5" y="{top}.5" width="{w - 1}" '
                f'height="{h}" fill="none" stroke="{fg}" stroke-width="1" '
                f'stroke-dasharray="1 1" opacity="0.5"/>'
            )
            continue
        g = p.glyph
        top = baseline - (g.bby + g.bbh)
        for rx, ry, rl in _glyph_runs(g):
            parts.append(
                f'<rect x="{p.x + g.bbx + rx}" y="{top + ry}" width="{rl}" '
                f'height="1" fill="{fg}"/>'
            )
    parts.append("</svg>")
    return "".join(parts)


_PAPER = (250, 247, 240)
_INK = (24, 22, 20)
_ACCENT = (195, 39, 43)


def _raster_image(f: ParsedFont, text: str, ink=_INK, paper=None):
    from PIL import Image

    placed, width, height = _layout(f, text)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0) if paper is None else (*paper, 255))
    px = img.load()
    for p in placed:
        baseline = p.line * (f.ascent + f.descent + LINE_GAP) + f.ascent
        if p.glyph is None:
            continue
        g = p.glyph
        top = baseline - (g.bby + g.bbh)
        for rx, ry, rl in _glyph_runs(g):
            for i in range(rl):
                x, y = p.x + g.bbx + rx + i, top + ry
                if 0 <= x < width and 0 <= y < height:
                    px[x, y] = (*ink, 255)
    return img


def og_png(f: ParsedFont, name: str, text: str, out: Path) -> None:
    from PIL import Image

    W, H = 1200, 630
    canvas = Image.new("RGB", (W, H), _PAPER)
    # 顶部朱砂色条
    for y in range(0, 12):
        for x in range(W):
            canvas.putpixel((x, y), _ACCENT)

    def paste_scaled(img, target_h: int, y: int) -> None:
        if img.width == 0 or img.height == 0:
            return
        scale = max(1, min(target_h // max(1, img.height), (W - 120) // max(1, img.width)))
        big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        x = max(0, (W - big.width) // 2)
        canvas.paste(big, (x, y), big)

    name_img = _raster_image(f, name)
    sample_img = _raster_image(f, text)
    paste_scaled(name_img, 220, 110)
    paste_scaled(sample_img, 180, 380)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, format="PNG")
