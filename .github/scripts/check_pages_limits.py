"""Check the complete publish directory against Cloudflare Pages Free limits."""
import argparse
from pathlib import Path


def check(root: Path, max_files: int = 20000, max_bytes: int = 25 * 1024**2) -> dict:
    files = [(p, p.stat().st_size) for p in root.rglob("*") if p.is_file()]
    if not files:
        raise ValueError(f"Publish directory is empty: {root}")
    large = [(str(p.relative_to(root)), size) for p, size in files if size > max_bytes]
    if len(files) > max_files or large:
        raise ValueError(f"Pages Free limit exceeded: {len(files)}/{max_files} files; oversized files: {large}")
    return {"files": len(files), "bytes": sum(size for _, size in files),
            "max_bytes": max(size for _, size in files), "file_headroom": max_files - len(files)}


if __name__ == "__main__":
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.directory), indent=2))
