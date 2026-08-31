"""把 dist-downloads/ 增量同步到 Cloudflare R2。

比对依据是 dist-downloads/manifest.json 里的 sha256，与对象上存的
x-amz-meta-sha256 逐一对照：新增/变更才上传，线上多余的删除。
不靠 mtime 或大小——CI 每次跑 mtime 都是新的，而大小相同内容不同的情况
真实存在（TTF 改一个字形通常不改变文件长度）。

之所以能这么比，前提是构建产物本身是字节确定的：TTF 的 head 时间戳被固定
成常量，同样的输入产出同样的字节。否则每次构建都会变成全量重传 1.4GB。

需要环境变量：
    R2_ACCOUNT_ID  R2_ACCESS_KEY_ID  R2_SECRET_ACCESS_KEY
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

CONTENT_TYPES = {
    ".ttf": "font/ttf",
    ".gz": "application/gzip",
    ".zip": "application/zip",
    ".json": "application/json",
}


def content_type(name: str) -> str:
    return CONTENT_TYPES.get(Path(name).suffix.lower(), "application/octet-stream")


def main() -> int:
    ap = argparse.ArgumentParser(description="增量同步下载物到 R2")
    ap.add_argument("--dir", type=Path, required=True)
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--prefix", default="", help="对象名前缀，默认放在桶根")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import boto3
    from botocore.config import Config

    account = os.environ["R2_ACCOUNT_ID"]
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{account}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        region_name="auto",
        config=Config(retries={"max_attempts": 5, "mode": "standard"}),
    )

    manifest = json.loads((args.dir / "manifest.json").read_text(encoding="utf-8"))
    local = {e["file"]: e["sha256"] for e in manifest["entries"]}
    local["manifest.json"] = ""  # 清单本身也上传，但每次都覆盖

    remote: dict[str, str] = {}
    token = None
    while True:
        kw = {"Bucket": args.bucket, "Prefix": args.prefix}
        if token:
            kw["ContinuationToken"] = token
        page = s3.list_objects_v2(**kw)
        for obj in page.get("Contents", []):
            key = obj["Key"][len(args.prefix):]
            head = s3.head_object(Bucket=args.bucket, Key=obj["Key"])
            remote[key] = head.get("Metadata", {}).get("sha256", "")
        if not page.get("IsTruncated"):
            break
        token = page.get("NextContinuationToken")

    put = [f for f, h in local.items() if remote.get(f) != h or not h]
    drop = [f for f in remote if f not in local]
    total = sum((args.dir / f).stat().st_size for f in put if (args.dir / f).exists())
    print(f"本地 {len(local)} 个，线上 {len(remote)} 个 → "
          f"上传 {len(put)}（{total / 1e6:.1f} MB），删除 {len(drop)}")
    if args.dry_run:
        return 0

    for f in put:
        path = args.dir / f
        if not path.exists():
            print(f"  跳过（本地不存在）: {f}", file=sys.stderr)
            continue
        s3.put_object(
            Bucket=args.bucket,
            Key=args.prefix + f,
            Body=path.read_bytes(),
            ContentType=content_type(f),
            Metadata={"sha256": local[f]} if local[f] else {},
        )
    for i in range(0, len(drop), 1000):
        s3.delete_objects(
            Bucket=args.bucket,
            Delete={"Objects": [{"Key": args.prefix + f} for f in drop[i:i + 1000]]},
        )
    print("同步完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
