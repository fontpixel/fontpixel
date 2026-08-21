"""把 dist-downloads/ 增量同步到滚动 Release(tag=downloads)。

依据本地 manifest.json 的 sha256 与线上已存在资产对比:
新增/变更 → 上传(--clobber);线上多余 → 删除。
依赖 gh CLI(GH_TOKEN 由 workflow 注入)。
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--tag", default="downloads")
    args = ap.parse_args()

    manifest_path = args.dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    local = {e["file"]: e["sha256"] for e in manifest["entries"]}

    view = gh("release", "view", args.tag, "--json", "assets", check=False)
    if view.returncode != 0:
        gh("release", "create", args.tag, "--title", "字体下载 Font downloads",
           "--notes", "由 CI 自动维护的滚动下载物;单个文件的校验值见站点。")
        remote_assets: list[dict] = []
    else:
        remote_assets = json.loads(view.stdout)["assets"]
    remote_names = {a["name"] for a in remote_assets}

    # 线上 manifest 决定哪些资产可跳过
    prev: dict[str, str] = {}
    if "manifest.json" in remote_names:
        dl = gh("release", "download", args.tag, "--pattern", "manifest.json",
                "--output", "-", check=False)
        if dl.returncode == 0:
            try:
                prev = {e["file"]: e["sha256"]
                        for e in json.loads(dl.stdout)["entries"]}
            except (json.JSONDecodeError, KeyError):
                prev = {}

    to_upload = [f for f, sha in local.items()
                 if prev.get(f) != sha or f not in remote_names]
    to_delete = [n for n in remote_names
                 if n not in local and n != "manifest.json"]

    print(f"upload: {len(to_upload)}, delete: {len(to_delete)}, "
          f"unchanged: {len(local) - len(to_upload)}")
    for name in to_delete:
        gh("release", "delete-asset", args.tag, name, "--yes")
    batch = [str(args.dir / f) for f in to_upload]
    for i in range(0, len(batch), 20):
        gh("release", "upload", args.tag, *batch[i : i + 20], "--clobber")
    gh("release", "upload", args.tag, str(manifest_path), "--clobber")
    print("done", file=sys.stderr)


if __name__ == "__main__":
    main()
