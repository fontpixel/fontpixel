"""家族级增量缓存:键 = 字表数据哈希 + 管线版本 + 源文件哈希。"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import fbf


def data_dir_hash(data_dir: Path) -> str:
    h = hashlib.sha256()
    h.update(f"pipeline:{fbf.PIPELINE_VERSION}".encode())
    for p in sorted(data_dir.rglob("*.txt")):
        h.update(p.relative_to(data_dir).as_posix().encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def family_key(data_hash: str, family_dir: Path, font_files: list[Path]) -> str:
    """键覆盖家族目录内全部文件(字体、toml、许可证等),任一变化即重建。"""
    h = hashlib.sha256()
    h.update(data_hash.encode())
    for p in sorted(family_dir.iterdir()):
        if not p.is_file():
            continue
        h.update(p.name.encode())
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


class FamilyCache:
    def __init__(self, cache_dir: Path):
        self.dir = cache_dir / "families"
        self.dir.mkdir(parents=True, exist_ok=True)

    def load(self, slug: str, key: str) -> dict | None:
        p = self.dir / f"{slug}.json"
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if data.get("key") != key:
            return None
        return data

    def store(self, slug: str, payload: dict) -> None:
        (self.dir / f"{slug}.json").write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
