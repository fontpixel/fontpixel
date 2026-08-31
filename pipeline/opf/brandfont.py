"""站名 web 字体：把站名用到的字符从馆藏像素字体子集成一个小字体。

页头站名此前用 canvas 逐页渲染（取字形包 → 光栅化 → 换掉文字），每次翻页
都闪一下。改成构建期产出 brand.woff2（几 KB，全站缓存一份），页头回归纯
文本。字符清单的唯一来源是 site/src/i18n/sitenames.json——站点的 i18n 与
本脚本读同一份，站名一改，两边同时跟上。

家族名叫 FBF Brand 而不是 Fusion Pixel：OFL 的保留字体名条款要求修改版
改名，子集属于修改。
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from opf.parsers.bdf import parse_bdf
from opf.vectorize import build_vector_ttf

# 候选源，按偏好排序；取第一个存在且全覆盖站名字符集的。
# fusion-pixel 各语言变体字符集相同（只有汉字字形随语言变），任选其一即可。
SOURCES = (
    "fusion-pixel/fusion-pixel-12px-proportional-zh_hans.bdf",
    "unifont-ex/unifont-ex.bdf",   # 兜底：什么都有，但字面大一号
)


def build_brand_font(fonts_dir: Path, data_dir: Path, names_path: Path) -> dict:
    names = json.loads(names_path.read_text(encoding="utf-8"))
    cps = {ord(c) for text in names.values() for c in text if not c.isspace()}

    for rel in SOURCES:
        src = fonts_dir / rel
        if not src.exists():
            continue
        font = parse_bdf(src, src.parent.name)
        have = {g.cp for g in font.glyphs}
        if cps <= have:
            break
        missing = "".join(chr(c) for c in sorted(cps - have))
        print(f"  brandfont: {rel} 缺 {missing}，试下一个候选")
    else:
        raise SystemExit(f"brandfont: 没有候选字体能覆盖站名字符集")

    font.glyphs = [g for g in font.glyphs if g.cp in cps]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / "brand.ttf"
        build_vector_ttf(
            font, "FBF Brand", "Regular", tmp, shape="square",
            copyright_=f"Subset of {src.parent.name} (OFL-1.1) for the site wordmark",
        )
        from fontTools.ttLib import TTFont

        f = TTFont(tmp, recalcTimestamp=False)
        try:
            f.flavor = "woff2"
            out_name = "brand.woff2"
            f.save(data_dir / out_name)
        except ImportError:            # 环境没有 brotli 时退回 woff（zlib 必有）
            f.flavor = "woff"
            out_name = "brand.woff"
            f.save(data_dir / out_name)

    meta = {"file": out_name, "px": font.pixel_size, "family": "FBF Brand",
            "source": src.name, "glyphs": len(font.glyphs)}
    (data_dir / "brand.json").write_text(
        json.dumps(meta, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    size = (data_dir / out_name).stat().st_size
    print(f"  brandfont: {out_name} {size/1024:.1f}KB，{len(font.glyphs)} 字形，"
          f"源 {src.name}")
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--names", type=Path, required=True)
    a = ap.parse_args()
    build_brand_font(a.fonts, a.data, a.names)


if __name__ == "__main__":
    main()
