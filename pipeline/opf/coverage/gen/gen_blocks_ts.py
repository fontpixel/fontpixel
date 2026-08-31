"""Generate a frontend block-range table from UCD Blocks.txt.

The glyph overview's "Jump to block" dropdown needs to list the Unicode blocks
a font covers, but detail.json's unicodeBlocks only has names and counts, no
code point ranges. The range data already lives in the pipeline's Blocks.txt,
so generate the TS directly here rather than maintaining a second copy.

    python -m opf.coverage.gen.gen_blocks_ts
"""

from __future__ import annotations

from pathlib import Path

from opf.coverage.ucd import load_ucd

HEADER = """// 由 `python -m opf.coverage.gen.gen_blocks_ts` 生成，请勿手改。
// 来源：UCD Blocks.txt（与管线的覆盖率统计同一份数据）。

/** Unicode block 名 → [起始码位, 结束码位]（含两端）。 */
export const UNICODE_BLOCKS: Record<string, readonly [number, number]> = {
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1] / "data" / "ucd"
    ucd = load_ucd(root)
    out = Path(__file__).resolve().parents[4] / "site" / "src" / "lib" / "unicodeblocks.ts"
    lines = [HEADER]
    for name, start, end in ucd.blocks:
        lines.append(f"  {name!r}: [0x{start:04X}, 0x{end:04X}],\n".replace("'", '"', 2))
    lines.append("};\n")
    out.write_text("".join(lines), encoding="utf-8")
    print(f"{out}: {len(ucd.blocks)} 个 block")


if __name__ == "__main__":
    main()
