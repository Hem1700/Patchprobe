from __future__ import annotations

from pathlib import Path


def write_bytes(root: str, rel_path: str, data: bytes) -> str:
    path = Path(root) / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return str(path)


def read_bytes(root: str, rel_path: str) -> bytes:
    path = Path(root) / rel_path
    return path.read_bytes()
