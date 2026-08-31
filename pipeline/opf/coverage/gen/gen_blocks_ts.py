"""由 UCD Blocks.txt 生成前端用的 block 区间表。

字形总览的「Jump to block」下拉要把字体覆盖到的 Unicode block 也列出来，
而 detail.json 里的 unicodeBlocks 只有名字和计数、没有码位区间。区间数据
就在管线已有的 Blocks.txt 里，这里直接生成 TS，避免两边各抄一份。

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
