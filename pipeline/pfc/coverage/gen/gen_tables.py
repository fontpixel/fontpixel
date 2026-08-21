"""字表数据生成器:编解码派生表、静态区间表、UCD、旧项目数据迁移。

运行(在仓库根):
    .venv/bin/python -m pfc.coverage.gen.gen_tables --all --old-dir <旧项目cjk-tables目录>

生成物直接写入 pfc/coverage/data/ 并入库;可重跑,输出确定。
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
TODAY = "2026-08-21"
UCD_BASE = "https://www.unicode.org/Public/17.0.0/ucd/"


def _ranges(cps: set[int]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for cp in sorted(cps):
        if out and cp == out[-1][1] + 1:
            out[-1] = (out[-1][0], cp)
        else:
            out.append((cp, cp))
    return out


def write_table(section: str, cid: str, order: int, name_zh: str, name_en: str,
                desc_zh: str, source: str, cps: set[int], license_: str = "") -> None:
    d = DATA / section
    d.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# id: {cid}",
        f"# section: {section}",
        f"# order: {order}",
        f"# name_zh: {name_zh}",
        f"# name_en: {name_en}",
        f"# desc_zh: {desc_zh}",
        "# desc_en: ",
        f"# source: {source}",
    ]
    if license_:
        lines.append(f"# license: {license_}")
    for a, b in _ranges(cps):
        lines.append(f"{a:04X}" if a == b else f"{a:04X}..{b:04X}")
    (d / f"{cid}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  {section}/{cid}: {len(cps)}")


# ---------------------------------------------------------------- codec 派生

def _row_cell(codec: str, rows: range, base: int = 0xA0) -> set[int]:
    cps: set[int] = set()
    for row in rows:
        for cell in range(1, 95):
            try:
                s = bytes([base + row, base + cell]).decode(codec)
            except UnicodeDecodeError:
                continue
            if len(s) == 1:
                cps.add(ord(s))
    return cps


def _is_han(cp: int) -> bool:
    return (
        0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF
        or 0xF900 <= cp <= 0xFAFF or 0x20000 <= cp <= 0x3FFFF
    )


def gen_codec_tables() -> None:
    src = f"Python codecs; generated {TODAY}"

    l1 = _row_cell("gb2312", range(16, 56))
    l2 = _row_cell("gb2312", range(56, 88))
    write_table("gb", "gb2312", 10, "GB/T 2312 汉字", "GB/T 2312 Hanzi",
                "1980 年国家标准基本集全部汉字,一二级合计 6763 字", src, l1 | l2)
    write_table("gb", "gb2312-l1", 11, "GB/T 2312 一级汉字", "GB/T 2312 Level 1 Hanzi",
                "一级常用字 3755 字,按拼音排序", src, l1)
    write_table("gb", "gb2312-l2", 12, "GB/T 2312 二级汉字", "GB/T 2312 Level 2 Hanzi",
                "二级次常用字 3008 字,按部首排序", src, l2)

    gbk: set[int] = set()
    for lead in range(0x81, 0xFF):
        for trail in list(range(0x40, 0x7F)) + list(range(0x80, 0xFF)):
            try:
                s = bytes([lead, trail]).decode("gbk")
            except UnicodeDecodeError:
                continue
            if len(s) == 1 and _is_han(ord(s)):
                gbk.add(ord(s))
    write_table("gb", "gbk-hanzi", 30, "GBK 汉字", "GBK Hanzi",
                "GBK 编码全部汉字(含兼容表意字)", src, gbk)

    b5_cy = set()
    b5_ci = set()
    for lead in range(0xA4, 0xFA):
        for trail in list(range(0x40, 0x7F)) + list(range(0xA1, 0xFF)):
            code = (lead << 8) | trail
            try:
                s = bytes([lead, trail]).decode("big5")
            except UnicodeDecodeError:
                continue
            if len(s) != 1:
                continue
            if 0xA440 <= code <= 0xC67E:
                b5_cy.add(ord(s))
            elif 0xC940 <= code <= 0xF9D5:
                b5_ci.add(ord(s))
    write_table("tw", "big5-changyong", 30, "五大码 (Big5) 常用汉字",
                "Big5 Frequently Used Hanzi", "Big5 常用字面 A440–C67E,5401 字", src, b5_cy)
    write_table("tw", "big5-cichangyong", 40, "五大码 (Big5) 次常用汉字",
                "Big5 Less Frequently Used Hanzi", "Big5 次常用字面 C940–F9D5", src, b5_ci)
    write_table("tw", "big5", 50, "五大码 (Big5) 全部汉字", "Big5 All Hanzi",
                "常用与次常用字面合计(按 Unicode 码位去重)", src, b5_cy | b5_ci)

    jis_nk = _row_cell("euc_jp", range(1, 16))
    jis1 = _row_cell("euc_jp", range(16, 48))
    jis2 = _row_cell("euc_jp", range(48, 85))
    write_table("jp", "jisx0208-nonkanji", 10, "JIS X 0208 非汉字",
                "JIS X 0208 Non-Kanji", "假名、符号、罗马/希腊/西里尔字母等", src, jis_nk)
    write_table("jp", "jisx0208-l1", 11, "JIS X 0208 第一水準漢字",
                "JIS X 0208 Level 1 Kanji", "第一水準 2965 字,按音读排序", src, jis1)
    write_table("jp", "jisx0208-l2", 12, "JIS X 0208 第二水準漢字",
                "JIS X 0208 Level 2 Kanji", "第二水準 3390 字,按部首排序", src, jis2)

    jis0208_kanji = jis1 | jis2
    p1: set[int] = set()
    p2: set[int] = set()
    plane2_rows = {1, 3, 4, 5, 8, 12, 13, 14, 15} | set(range(78, 95))
    for row in range(1, 95):
        for cell in range(1, 95):
            try:
                s = bytes([0xA0 + row, 0xA0 + cell]).decode("euc_jis_2004")
            except UnicodeDecodeError:
                continue
            if len(s) == 1:
                p1.add(ord(s))
            if row not in plane2_rows:
                continue  # Python codec 对未定义面2区回退 JIS X 0212,须排除
            try:
                s2 = bytes([0x8F, 0xA0 + row, 0xA0 + cell]).decode("euc_jis_2004")
            except UnicodeDecodeError:
                continue
            if len(s2) == 1:
                p2.add(ord(s2))
    l3 = {cp for cp in p1 if _is_han(cp) and cp not in jis0208_kanji}
    l4 = {cp for cp in p2 if _is_han(cp)}
    write_table("jp", "jisx0213-l3", 13, "JIS X 0213 第三水準漢字",
                "JIS X 0213 Level 3 Kanji", "2000/2004 年扩充,第一面新增汉字", src, l3)
    write_table("jp", "jisx0213-l4", 14, "JIS X 0213 第四水準漢字",
                "JIS X 0213 Level 4 Kanji", "第二面汉字", src, l4)

    kr_sym = _row_cell("euc_kr", range(1, 13))
    kr_hangul = _row_cell("euc_kr", range(16, 41))
    kr_hanja = _row_cell("euc_kr", range(42, 94))
    write_table("kr", "ksx1001-symbols", 30, "KS X 1001 符号",
                "KS X 1001 Symbols", "符号、字母、日文假名等非谚文非汉字部分", src, kr_sym)
    write_table("kr", "ksx1001-hangul", 10, "KS X 1001 谚文音节",
                "KS X 1001 Hangul Syllables", "现代韩语常用音节 2350 个", src, kr_hangul)
    write_table("kr", "ksx1001-hanja", 20, "KS X 1001 汉字",
                "KS X 1001 Hanja", "韩文汉字 4888 个(重复汉字映射至兼容区)", src, kr_hanja)

    cp437 = set()
    graphics = [0x263A, 0x263B, 0x2665, 0x2666, 0x2663, 0x2660, 0x2022, 0x25D8,
                0x25CB, 0x25D9, 0x2642, 0x2640, 0x266A, 0x266B, 0x263C, 0x25BA,
                0x25C4, 0x2195, 0x203C, 0x00B6, 0x00A7, 0x25AC, 0x21A8, 0x2191,
                0x2193, 0x2192, 0x2190, 0x221F, 0x2194, 0x25B2, 0x25BC]
    cp437.update(graphics)
    cp437.add(0x2302)  # 0x7F ⌂
    cp437.update(range(0x20, 0x7F))
    for b in range(0x80, 0x100):
        cp437.add(ord(bytes([b]).decode("cp437")))
    write_table("intl", "cp437", 70, "IBM 代码页 437", "IBM Code Page 437",
                "DOS/复古终端字符集(图形解释,0x01–0xFF 共 255 字符)",
                f"Python cp437 codec + IBM graphic set; generated {TODAY}", cp437)


# ---------------------------------------------------------------- 静态区间

def gen_static_tables() -> None:
    src = f"Unicode block ranges; generated {TODAY}"
    write_table("prc-lit", "kangxi-radicals", 60, "康熙部首", "Kangxi Radicals",
                "U+2F00–2FD5 全部 214 个部首", src, set(range(0x2F00, 0x2FD6)))
    write_table("prc-lit", "radicals-supplement", 61, "汉字部首补充",
                "CJK Radicals Supplement", "U+2E80–2EF3 中已指派的 115 个变形部首", src,
                set(range(0x2E80, 0x2E9A)) | set(range(0x2E9B, 0x2EF4)))
    write_table("tw", "bopomofo", 60, "注音符号", "Bopomofo",
                "注音符号及扩展(闽南语/客家语用)", src,
                set(range(0x3105, 0x3130)) | set(range(0x31A0, 0x31C0)))
    write_table("jp", "hiragana", 20, "平假名", "Hiragana",
                "U+3041–3096 全部平假名字母", src, set(range(0x3041, 0x3097)))
    write_table("jp", "katakana", 21, "片假名", "Katakana",
                "U+30A1–30FA 全部片假名字母", src, set(range(0x30A1, 0x30FB)))
    write_table("jp", "halfwidth-kana", 22, "半角假名", "Halfwidth Katakana",
                "U+FF61–FF9F 半角片假名与标点", src, set(range(0xFF61, 0xFFA0)))
    write_table("jp", "jisx0201", 23, "JIS X 0201", "JIS X 0201",
                "罗马字与半角假名(7 位/8 位单字节集)", src,
                set(range(0x20, 0x7F)) | set(range(0xFF61, 0xFFA0)))
    write_table("kr", "hangul-syllables", 40, "现代谚文音节(全部)",
                "Hangul Syllables (All Modern)", "U+AC00–D7A3 全部 11172 个音节", src,
                set(range(0xAC00, 0xD7A4)))
    write_table("kr", "hangul-compat-jamo", 50, "谚文兼容字母",
                "Hangul Compatibility Jamo", "U+3131–318E 谚文兼容字母", src,
                set(range(0x3131, 0x318F)))
    write_table("kr", "hangul-jamo", 60, "谚文字母 (Jamo)", "Hangul Jamo",
                "U+1100–11FF 组合用谚文字母(含古谚文)", src, set(range(0x1100, 0x1200)))
    write_table("intl", "latin-basic", 30, "基本拉丁字母", "Basic Latin",
                "可打印 ASCII,U+0020–007E", src, set(range(0x20, 0x7F)))
    write_table("intl", "latin1-supp", 31, "拉丁字母-1 补充", "Latin-1 Supplement",
                "U+00A0–00FF,西欧语言字符", src, set(range(0xA0, 0x100)))
    write_table("intl", "latin-ext-a", 32, "拉丁字母扩展-A", "Latin Extended-A",
                "U+0100–017F,中东欧语言字符", src, set(range(0x100, 0x180)))
    write_table("intl", "latin-ext-b", 33, "拉丁字母扩展-B", "Latin Extended-B",
                "U+0180–024F", src, set(range(0x180, 0x250)))
    write_table("intl", "cyrillic", 40, "西里尔字母", "Cyrillic",
                "U+0400–04FF 基本区", src, set(range(0x400, 0x500)))
    write_table("intl", "box-drawing", 71, "制表符", "Box Drawing",
                "U+2500–257F,终端表格线", src, set(range(0x2500, 0x2580)))
    write_table("intl", "block-elements", 72, "方块元素", "Block Elements",
                "U+2580–259F,终端色块", src, set(range(0x2580, 0x25A0)))
    write_table("intl", "powerline", 73, "Powerline 符号", "Powerline Symbols",
                "私用区 U+E0A0–E0D4 中 Powerline 及其扩展占用的 41 个符号",
                f"powerline/fontpatcher 约定; generated {TODAY}",
                {0xE0A0, 0xE0A1, 0xE0A2, 0xE0A3} | set(range(0xE0B0, 0xE0B4))
                | set(range(0xE0B4, 0xE0D5)))
    write_table("intl", "braille", 74, "盲文点字", "Braille Patterns",
                "U+2800–28FF 全部 256 个盲文图案", src, set(range(0x2800, 0x2900)))


# ---------------------------------------------------------------- UCD

def gen_ucd() -> None:
    ucd_dir = DATA / "ucd"
    ucd_dir.mkdir(parents=True, exist_ok=True)
    blocks_txt = ucd_dir / "Blocks.txt"
    if not blocks_txt.exists():
        urllib.request.urlretrieve(UCD_BASE + "Blocks.txt", blocks_txt)
    unicodedata_txt = ucd_dir / "UnicodeData.txt.tmp"
    urllib.request.urlretrieve(UCD_BASE + "UnicodeData.txt", unicodedata_txt)

    assigned: set[int] = set()
    range_first: int | None = None
    for line in unicodedata_txt.read_text(encoding="utf-8").splitlines():
        fields = line.split(";")
        if len(fields) < 3:
            continue
        cp = int(fields[0], 16)
        name, cat = fields[1], fields[2]
        if cat == "Cs":
            continue
        if name.endswith(", First>"):
            range_first = cp
            continue
        if name.endswith(", Last>"):
            if range_first is not None:
                assigned.update(range(range_first, cp + 1))
                range_first = None
            continue
        assigned.add(cp)
    unicodedata_txt.unlink()

    lines = [
        "# Unicode 17.0.0 已指派码位(排除代理区 Cs;含 Co 私用区)",
        f"# source: {UCD_BASE}UnicodeData.txt; generated {TODAY}",
        "# license: Unicode License v3 (https://www.unicode.org/license.txt)",
    ]
    for a, b in _ranges(assigned):
        lines.append(f"{a:04X}" if a == b else f"{a:04X}..{b:04X}")
    (ucd_dir / "assigned-ranges.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ucd: {len(assigned)} assigned cps")


# ---------------------------------------------------------------- Unihan / 越南语

def gen_unihan_core() -> None:
    import io
    import zipfile

    with urllib.request.urlopen(UCD_BASE + "Unihan.zip") as resp:
        z = zipfile.ZipFile(io.BytesIO(resp.read()))
    cps: set[int] = set()
    with z.open("Unihan_DictionaryLikeData.txt") as fh:
        for line in io.TextIOWrapper(fh, encoding="utf-8"):
            if "\tkUnihanCore2020\t" in line:
                cps.add(int(line.split("\t")[0][2:], 16))
    write_table("intl", "unihan-core-2020", 11, "UnihanCore2020 核心集",
                "Unihan Core 2020",
                "Unihan 数据库定义的现代通用核心汉字集,覆盖中日韩越及港台用字",
                f"{UCD_BASE}Unihan.zip kUnihanCore2020; generated {TODAY}", cps,
                license_="Unicode License v3")


def gen_greek() -> None:
    from pfc.coverage.ucd import load_ucd

    u = load_ucd(DATA / "ucd")
    cps = {cp for cp in range(0x370, 0x400) if cp in u.assigned}
    write_table("intl", "greek-coptic", 41, "希腊和科普特字母", "Greek and Coptic",
                "U+0370–03FF 区段中已指派的字符",
                f"Unicode 17.0 Blocks/UnicodeData; generated {TODAY}", cps)


def gen_viet() -> None:
    upper_l1 = [0xC0, 0xC1, 0xC2, 0xC3, 0xC8, 0xC9, 0xCA, 0xCC, 0xCD,
                0xD2, 0xD3, 0xD4, 0xD5, 0xD9, 0xDA, 0xDD]
    ext = [0x102, 0x103, 0x110, 0x111, 0x128, 0x129, 0x168, 0x169,
           0x1A0, 0x1A1, 0x1AF, 0x1B0]
    cps: set[int] = set(range(0x41, 0x5B)) | set(range(0x61, 0x7B))
    cps.update(upper_l1)
    cps.update(c + 0x20 for c in upper_l1)
    cps.update(ext)
    cps.update(range(0x1EA0, 0x1EFA))
    write_table("intl", "viet-latin", 50, "越南语拉丁字符", "Vietnamese Latin",
                "越南语国语字全部字母:基本拉丁 + 带符字母(Latin-1/扩展 A/B)"
                " + 拉丁扩展附加 U+1EA0–1EF9",
                f"按 Unicode 越南语用字构成定义; generated {TODAY}", cps)


# ---------------------------------------------------------------- 旧数据迁移

_MIGRATE = {
    "tongyong-guifan-han.txt": ("prc-lit", "tongyong-guifan", 10, "通用规范汉字表",
        "Table of General Standard Chinese Characters",
        "2013 年国务院发布的现行规范,8105 字,分三级"),
    "3500changyong-han.txt": ("prc-lit", "changyong-3500", 20, "现代汉语常用字表",
        "List of Frequently Used Characters in Modern Chinese",
        "1988 年发布,常用 2500 字与次常用 1000 字"),
    "7000tongyong-han.txt": ("prc-lit", "tongyong-7000", 30, "现代汉语通用字表",
        "List of Commonly Used Characters in Modern Chinese", "1988 年发布,7000 字"),
    "yiwu-jiaoyu-han.txt": ("prc-lit", "yijiao-3500", 40, "义务教育语文课程常用字表",
        "Compulsory Education Chinese Character List", "2022 年版课程标准附录,3500 字"),
    "gujiyinshua-han.txt": ("prc-lit", "guji-yinshua", 50, "古籍印刷通用字规范字形表",
        "Standard Glyphs for Ancient Books Printing", "2021 年发布的古籍印刷用字规范"),
    "gb12345-han.txt": ("gb", "gb12345", 40, "GB/T 12345 繁体字符集",
        "GB/T 12345 Traditional Hanzi", "1990 年发布,与 GB/T 2312 对应的繁体集"),
    "iicore-han.txt": ("intl", "iicore", 10, "国际表意文字核心集 (IICore)",
        "International Ideographs Core (IICore)",
        "ISO/IEC 10646 附录,面向资源受限环境的核心汉字集合"),
    "hanyi-jianfan-han.txt": ("prc-lit", "hanyi-jianfan", 90, "汉仪简繁字表",
        "HanYi Simplified & Traditional Set", "字库厂商汉仪的简繁覆盖口径"),
    "fangzheng-jianfan-han.txt": ("prc-lit", "fangzheng-jianfan", 91, "方正简繁字表",
        "FounderType Simplified & Traditional Set", "字库厂商方正的简繁覆盖口径"),
    "4808changyong-han.txt": ("tw", "tw-changyong-4808", 10, "常用国字标准字体表",
        "Standard Forms of Common National Characters", "台湾地区甲表,4808 字"),
    "6343cichangyong-han.txt": ("tw", "tw-cichangyong-6343", 20, "次常用国字标准字体表",
        "Standard Forms of Less-Common National Characters", "台湾地区乙表,6343 字"),
    "hkchangyong-han.txt": ("hk", "hk-changyong", 10, "常用字字形表",
        "List of Graphemes of Commonly-Used Chinese Characters", "香港教育局字形表"),
    "hkscs-han.txt": ("hk", "hkscs", 20, "香港增补字符集 (HKSCS) 汉字",
        "Hong Kong Supplementary Character Set Hanzi", "HKSCS-2016 汉字部分"),
    "suppchara-han.txt": ("hk", "hk-suppchara", 30, "常用香港外字表",
        "Hong Kong Supplementary Characters in Common Use", "教育局常用外字(1–6 级)"),
}


def migrate_old(old_dir: Path) -> None:
    src = f"CJK-character-count project data, migrated {TODAY}"
    for fname, (section, cid, order, zh, en, desc) in _MIGRATE.items():
        p = old_dir / fname
        if not p.exists():
            print(f"  !! missing {fname}")
            continue
        text = p.read_text(encoding="utf-8")
        parts = text.split("---")
        body = parts[2] if len(parts) >= 3 else text
        cps = {ord(ch) for line in body.splitlines() for ch in line.strip()}
        write_table(section, cid, order, zh, en, desc, src, cps,
                    license_="MIT (CJK-character-count, © NFSL2001)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--old-dir", type=Path, default=None)
    args = ap.parse_args()
    if args.all:
        print("UCD:")
        gen_ucd()
        print("codec tables:")
        gen_codec_tables()
        print("static tables:")
        gen_static_tables()
        print("unihan/viet/greek:")
        gen_unihan_core()
        gen_viet()
        gen_greek()
        if args.old_dir:
            print("migrate:")
            migrate_old(args.old_dir)


if __name__ == "__main__":
    main()
