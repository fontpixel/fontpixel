"""搬迁 bdfparser_js / bdfparser_py（含 typedoc api 子树），围栏感知。"""
import re
from pathlib import Path

COLLECTED = []  # (demo_id, props_text, func_text)

SRC = Path("../pixel-font-collection-fonts/github-clones-2026-08-31/tomchen-font-website-local")
DST = Path("site/src/content/docs")

MAIN = {
    "bdfparser-js": ("bdfparser_js", ["index", "font", "glyph", "bitmap"]),
    "bdfparser-py": ("bdfparser_py", ["index", "font", "glyph", "bitmap"]),
}
IMPORTS = {
    "<Tabs": "import Tabs from '@dc/Tabs.astro';",
    "<TabItem": "import TabItem from '@dc/TabItem.astro';",
    "<Tooltip": "import Tooltip from '@dc/Tooltip.astro';",
    "<Figure": "import Figure from '@dc/Figure.astro';",
    "<Keyword": "import Keyword from '@dc/Keyword.astro';",
    "<Aside": "import Aside from '@dc/Aside.astro';",
    "<BDF": "import BDF from '@dc/BDF.svelte';",
}

def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)

def fmval(fm, key):
    m = re.search(rf"^{key}:\s*(.+)$", fm, re.M)
    return m.group(1).strip().strip("'\"") if m else None

def outside_fences(body, fn):
    """只对代码围栏之外的行应用 fn（逐行）。"""
    out, fence = [], False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append(line)
        else:
            out.append(line if fence else fn(line))
    return "\n".join(out)

def fix_rel_links(line, is_index, depth=1, is_md=False):
    """相对文档链接 → 目录式 URL（非 index 页要多退一级）。

    depth：当前页面 URL 在 /{lang}/ 之下的目录层数（index 页为 1）。
    跨区块链接（../bdf_spec 等）一律重写成从页面 URL 回退 depth 层再进目标区块。"""
    SECTION_MAP = {"bdf_spec": "bdf-spec", "bdfparser_js": "bdfparser-js", "bdfparser_py": "bdfparser-py", "font_template": "font-template"}
    ASSET_EXT = re.compile(r"\.(png|jpe?g|svg|gif|webp|bdf|zip|pdf|ttf|woff2?)$", re.I)
    def rep(m):
        target = m.group(1)
        if re.match(r"^(https?:|mailto:|/|#)", target):
            return m.group(0)
        path, _, anchor = target.partition("#")
        if ASSET_EXT.search(path):
            return m.group(0)
        path = re.sub(r"\.(md|mdx)$", "", path)
        if not path:
            return m.group(0)
        suffix = f"#{anchor}" if anchor else ""
        if path.startswith("."):
            # typedoc 生成的 .md 按文件相对写链接；页面 URL 比文件多一层目录
            if is_md and not is_index:
                path = "../" + path
            for old_slug, new_slug in SECTION_MAP.items():
                path = re.sub(rf"(^|/){old_slug}(?=/|$)", rf"\g<1>{new_slug}", path)
            if not path.endswith("/"):
                path += "/"
            # 跨区块：原文按文件相对写（../bdf_spec/…），改成从页面 URL 回退 depth 层
            m2 = re.match(r"^(\.\./)+((bdf-spec|bdfparser-js|bdfparser-py|font-template)/.*)$", path)
            if m2:
                path = "../" * depth + m2.group(2)
            return f"]({path}{suffix})"
        pre = "" if is_index else "../"
        return f"]({pre}{path}/{suffix})"
    return re.sub(r"\]\(([^)\s]+)\)", rep, line)


def _sub_outside_inline_code(seg, bdf_rep):
    """对段落做 <BDF func={…}/> 替换，但跳过行内反引号代码。"""
    parts = re.split(r"(`[^`\n]*`)", seg)
    return "".join(
        part if i % 2 else re.sub(r"<BDF\s*([^>]*?)func=\{(.*?)\}\s*/>", bdf_rep, part, flags=re.S)
        for i, part in enumerate(parts))

def convert(text, order, entry_key, is_index, is_md):
    fm, body = split_fm(text)
    title = fmval(fm, "title") or "Untitled"
    label = fmval(fm, "sidebar_label")

    lines_out, fence = [], False
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            lines_out.append(line)
            continue
        if not fence and re.match(r"^import .+ from '(@site|@theme|@docusaurus)", line):
            continue  # 原站组件导入全部剥掉，按用法重加
        lines_out.append(line)
    body = "\n".join(lines_out)

    # typedoc .md 的正文重复 H1（原站用 hide_title 藏掉），这里由布局出标题
    if is_md:
        body = re.sub(r"^\s*# .+\n", "", body, count=1)

    # 活演示：抽出 func 与属性进注册表，MDX 只留 <BDF demo="…" />
    # 必须按围栏分块——代码示例里的 <BDF> 是给读者看的原文，不能替换
    page_tag = entry_key.replace("bdfparser-", "").replace("/", "-")
    counter = [0]
    def bdf_rep(m):
        n = counter[0]; counter[0] += 1
        demo_id = f"{page_tag}-{n}"
        COLLECTED.append((demo_id, m.group(1), m.group(2)))
        return f'<BDF demo="{demo_id}" client:visible />'
    chunks, fence, cur = [], False, []
    for line in body.split("\n"):
        if line.lstrip().startswith("```"):
            chunks.append((fence, "\n".join(cur))); cur = [line]; fence = not fence
            continue
        cur.append(line)
    chunks.append((fence, "\n".join(cur)))
    body = "\n".join(
        seg if in_fence else _sub_outside_inline_code(seg, bdf_rep)
        for in_fence, seg in chunks)

    # MDX1 的转义泛型 <string\> 在 MDX3 里是非法 JSX，改成 HTML 实体；由内向外迭代处理嵌套
    def _fix_generics(line):
        prev = None
        while prev != line:
            prev = line
            line = re.sub(r"<(?=[A-Za-z])([^<>]*?)\\>", r"&lt;\1&gt;", line)
        return line
    body = outside_fences(body, _fix_generics)
    # MDX3 要求 <details> 独占一行成为块级 JSX，内联开标签会报未闭合
    body = outside_fences(body, lambda l: l.replace("<details><summary>", "<details>\n<summary>"))
    slug = re.sub(r"\.(md|mdx)$", "", entry_key)
    slug = re.sub(r"(^|/)index$", "", slug).rstrip("/")
    depth = slug.count("/") + 1  # URL 在 /{lang}/ 之下的目录层数：section/ → 1，section/page/ → 2，section/api/a/b/ → 4
    body = outside_fences(body, lambda l: fix_rel_links(l, is_index, depth, is_md))
    # useBaseUrl('x') → BASE_URL 拼接
    body = body.replace("useBaseUrl('", "import.meta.env.BASE_URL + ('")
    body = re.sub(r"import\.meta\.env\.BASE_URL \+ \('([^']+)'\)",
                  r"import.meta.env.BASE_URL + '\1'", body)

    if not is_md:  # .md 不支持组件，也不会用到
        needed = [imp for probe, imp in IMPORTS.items() if re.search(rf"{re.escape(probe)}[\s>]", body)]  # 行内组件（如 Tooltip）也要认
        if needed:
            body = "\n".join(needed) + "\n\n" + body.lstrip("\n")

    esc = lambda v: v.replace('"', '\\"')
    out = ["---", f'title: "{esc(title)}"']
    if label:
        out.append(f'label: "{esc(label)}"')
    out.append(f"order: {order}")
    out.append("---")
    return "\n".join(out) + "\n\n" + body.lstrip("\n")

for section, (src_dir, pages) in MAIN.items():
    for order, page in enumerate(pages):
        sp = SRC / src_dir / f"{page}.mdx"
        dp = DST / section / f"{page}.mdx"
        dp.parent.mkdir(parents=True, exist_ok=True)
        key = f"{section}/{page}"
        dp.write_text(convert(sp.read_text(encoding="utf-8"), order, key, page == "index", False), encoding="utf-8")
        print(f"  {key}")

# typedoc api 子树（仅 js 有）
api_files = sorted((SRC / "bdfparser_js" / "api").rglob("*.md"))
for n, sp in enumerate(api_files):
    rel = sp.relative_to(SRC / "bdfparser_js")           # api/classes/font.md
    dp = DST / "bdfparser-js" / rel
    dp.parent.mkdir(parents=True, exist_ok=True)
    is_index = sp.name == "index.md"
    order = 10 + n
    text = convert(sp.read_text(encoding="utf-8"), order, f"bdfparser-js/{rel}", is_index, True)
    # 侧栏里给 API 项加前缀，便于与正文区分
    text = re.sub(r'^label: "(.*)"$', lambda m: f'label: "API · {m.group(1)}"', text, count=1, flags=re.M)
    dp.write_text(text, encoding="utf-8")
    print(f"  bdfparser-js/{rel}")
print("done")


# ---- 生成活演示注册表 ----
def parse_props(txt):
    out = {}
    m = re.search(r"fontfile='([^']+)'", txt)
    if m:
        out["fontfile"] = m.group(1).rsplit("/", 1)[-1]
    m = re.search(r"size=\{(\d+)\}", txt)
    if m:
        out["size"] = m.group(1)
    m = re.search(r"pixelcolors=\{(\{.*?\})\}", txt, re.S)
    if m:
        out["pixelcolors"] = m.group(1)
    return out

rows = []
for demo_id, props_txt, func_txt in COLLECTED:
    props = parse_props(props_txt)
    fields = [f"fn: {func_txt.strip()}"]
    if "fontfile" in props:
        fields.append(f"fontfile: '{props['fontfile']}'")
    if "size" in props:
        fields.append(f"size: {props['size']}")
    if "pixelcolors" in props:
        fields.append(f"pixelcolors: {props['pixelcolors']}")
    rows.append(f"  '{demo_id}': {{\n    " + ",\n    ".join(fields) + ",\n  },")
gen = (
    "/* eslint-disable */\n"
    "// 由 port_docs2.py 从原站 MDX 的 <BDF func={…}> 用法生成；改动演示请改这里。\n"
    "/** 单个活演示：fn 收到已加载的 Font 与 bdfparser 各类的集合。 */\n"
    "export interface BdfDemo {\n"
    "  fn: (font: any, ctx: any) => any;\n"
    "  fontfile?: string;\n"
    "  size?: number;\n"
    "  pixelcolors?: Record<number, string | null>;\n"
    "}\n\n"
    "export const DEMOS: Record<string, BdfDemo> = {\n" + "\n".join(rows) + "\n};\n")
Path("site/src/components/docs/bdfdemos.gen.ts").write_text(gen, encoding="utf-8")
print(f"注册表：{len(COLLECTED)} 个演示")
