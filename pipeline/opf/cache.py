"""家族级增量缓存：条目存「事实」，命中判定在比对时套用政策。

事实 = 字表数据哈希（含管线版本）+ 家族目录里每个文件的哈希 + family.toml
的完整解析快照。政策 = 哪些 toml 字段算「结构性」（_STRUCTURAL_KEYS），
只活在代码里，facts_match 比对时才把它套到存档快照与当前文件上。

为什么不存一个算好的键：键算法一变（哪怕只是调整结构性字段清单），所有
不透明哈希就全部对不上，唯一的解药是记得跑迁移脚本——2026-08-30 就因为
忘了跑而付出 52 分钟全量重建。存事实则没有这个失效模式：政策改了，两边
都按新政策取子集，值没变就照样命中。
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from pathlib import Path

import opf


def data_dir_hash(data_dir: Path) -> str:
    h = hashlib.sha256()
    h.update(f"pipeline:{opf.PIPELINE_VERSION}".encode())
    for p in sorted(data_dir.rglob("*.txt")):
        h.update(p.relative_to(data_dir).as_posix().encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


# family.toml 里会改变「构建出什么」的键。其余字段纯粹是展示文本，
# 改了不必重算字形包、覆盖率与 TTF 轮廓——见 build.py 的快路径。
#
#   merge / merge_subsets / exclude  决定构建哪些字形
#   variants                         决定变体 id、尺寸、字重、排布
#   license                          决定许可证产物与 TTF 里的版权行
#   converted_from                   决定「转换自」标记
#   name                             被烘进 OG 图（只有它，各语言名都不进产物）
#   samples / sample_lang            样例文本的选取依赖字体实际覆盖，
#                                    没有解析好的字体算不出来
_STRUCTURAL_KEYS = (
    "merge", "merge_subsets", "exclude", "variants", "license",
    "converted_from", "name", "samples", "sample_lang",
)


def family_facts(data_hash: str, family_dir: Path) -> dict:
    """采集一个家族当前的全部事实，作为缓存条目的一部分存盘。

    family.toml 存解析后的快照而非哈希——命中判定要按「当时的政策」从中
    取结构性子集。解析不了（文件损坏）就存整文件哈希，保证既不误命中、
    也不会每次都重建同一个坏状态。
    """
    files: dict[str, str] = {}
    toml_snapshot: dict | None = None
    for p in sorted(family_dir.iterdir()):
        if not p.is_file():
            continue
        if p.name == "family.toml":
            try:
                raw = tomllib.loads(p.read_text(encoding="utf-8"))
                # 过一遍 JSON：日期等非 JSON 标量归一成字符串，让「现算的
                # 事实」与「从缓存条目读回的事实」逐位可比
                toml_snapshot = json.loads(
                    json.dumps(raw, ensure_ascii=False, sort_keys=True,
                               default=str))
            except (OSError, tomllib.TOMLDecodeError):
                toml_snapshot = {
                    "__unparseable__":
                        hashlib.sha256(p.read_bytes()).hexdigest()
                }
            continue
        files[p.name] = hashlib.sha256(p.read_bytes()).hexdigest()
    return {"data_hash": data_hash, "files": files, "toml": toml_snapshot}


def structural_subset(toml_snapshot: dict | None) -> str:
    """按当前政策取 toml 快照的结构性子集，规范化成可比字符串。"""
    if not isinstance(toml_snapshot, dict):
        return "__missing__"
    subset = {k: toml_snapshot[k] for k in _STRUCTURAL_KEYS
              if k in toml_snapshot}
    if "__unparseable__" in toml_snapshot:
        subset["__unparseable__"] = toml_snapshot["__unparseable__"]
    return json.dumps(subset, sort_keys=True, ensure_ascii=False, default=str)


def facts_match(stored: dict | None, current: dict) -> bool:
    """存档事实与当前事实是否等价（等价 ⇒ 字形产物可以复用）。

    文件逐个比哈希；family.toml 只比结构性子集——展示字段的变化由
    build.py 的快路径回填，不触发重建。
    """
    if not isinstance(stored, dict):
        return False
    return (
        stored.get("data_hash") == current["data_hash"]
        and stored.get("files") == current["files"]
        and structural_subset(stored.get("toml"))
            == structural_subset(current["toml"])
    )


class FamilyCache:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir / "families"
        self.dir.mkdir(parents=True, exist_ok=True)

    def load(self, slug: str, facts: dict) -> dict | None:
        p = self.dir / f"{slug}.json"
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not facts_match(data.get("facts"), facts):
            return None
        return data

    def store(self, slug: str, payload: dict) -> None:
        (self.dir / f"{slug}.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
